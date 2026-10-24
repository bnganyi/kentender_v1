# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""How an independently registered contract is funded (CM-CHG-001 v0.10 sections 5.13, 5.14, 20.4, 20.4A, 20.5, 20.6; BUD-CHG-001 v1.16 sections 8.6, 8.8; tracker CM-FUND).

A contract signed before KenTender has no Tender, Award or reservation here, so Budget never converts anything for it. Its funding goes one of two routes, and Contract Management owns the contract's side of both:

* **KenTender Budget controls the funding.** The head of procurement records the route with its authority evidence and the contract's year shares. Finance **approval** (never the Finance preparer of the same
  figures) confirms the exact funding charge for a target Budget year in the opening review: that confirmation is a versioned `ContractFundingBasis.v1` whose digest, evidence and confirmers travel to Budget.
  The head raises one request per contract and year (Initial for the first, Annual for a later year); Budget's Officer maps it to lines and a different Approver decides. Outcomes come back in order and say what
  happened; a later year needs its own request and its own confirmation, never a reopening of the contract and never an automatic carry-forward of an earlier year's liability.
* **Funding is controlled outside KenTender Budget.** The head confirms the responsible authority's evidence and Finance confirms the same through the same review. Until both are given the contract shows
  **Funding not confirmed**; after both, **Funded outside KenTender Budget**. Budget creates no request, entry or commitment for it.

Contract Management sends Budget validated funding facts and opaque evidence references only, and reads no Budget table. What Budget cannot fund holds the **affected unfunded scope** and nothing else: a payment for
a year with no confirmed funding, new spending and obligation increases while the current year is unfunded. Factual recording (arrival, claims, evidence, an existing liability) is never held. The hold is a provider on
the shared holds framework, so every Contract Management command, and the native payment guard, read the same answer."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_contracts.services import authority, clock, events, holds, people, preflight, records, segregation, work
from kentender_contracts.services.errors import fail, invalid
from kentender_core.services import contract_funding_request_contract as seam

RECORD = "Contract Funding Record"
CASE = "Contract Case"
ROUTE_BUDGET, ROUTE_OUTSIDE = "KenTender Budget", "Outside KenTender Budget"
ROUTES = (ROUTE_BUDGET, ROUTE_OUTSIDE)

S_YEAR_REQUIRED = "Year allocation required"
S_READY = "Ready to request funding"
S_PENDING = "Funding entry pending"
S_APPROVED = "Funding entry approved"
S_SHORTFALL = "Funding shortfall"
S_RETURNED = "Funding entry returned"
S_ALREADY = "Already covered — no new entry required"
S_NO_CHARGE = "No charge to this year"
S_FUTURE = "Future funding not yet confirmed"
S_SCOPE = "Funding scope needs review"
S_DECLINED = "Funding request declined"
S_WITHDRAWN = "Funding request withdrawn"
S_NOT_CONFIRMED = "Funding not confirmed"
S_OUTSIDE = "Funded outside KenTender Budget"
S_NOT_LINKED = "Not linked to KenTender Budget"

#: outcomes that mean the year's charge is covered and the scope is no longer held
COVERED = (seam.OUTCOME_APPROVED, seam.OUTCOME_ALREADY_COVERED, seam.OUTCOME_NO_CHARGE)
FUNDING_HOLD_BLOCKS = frozenset({"pay", "new_spending", "vary_contract"})


# ---- small helpers --------------------------------------------------------------------------------------------------------------


def _money(value: Any, label: str, field: str, *, allow_zero: bool = True) -> str:
	text = cstr(value).replace(",", "").strip()
	try:
		number = Decimal(text)
	except InvalidOperation:
		invalid({field: f"Enter {label.lower()} as an amount."})
		raise
	if not number.is_finite() or number != number.quantize(Decimal("0.01")) or number < 0 or (number == 0 and not allow_zero):
		invalid({field: f"Enter {label.lower()} as an amount of {'zero' if allow_zero else 'above zero'} or more, with at most two decimal places."})
	return f"{number.quantize(Decimal('0.01'))}"


def _external(doc) -> None:
	if doc.source_kind != "External record":
		fail("CM_CHANGED", reason="This contract came from a KenTender award, which is funded by its reservations.")


def fiscal_year_of(day) -> str:
	"""The Fiscal Year that contains a date, or an empty string."""
	if not day:
		return ""
	value = records.day(day)
	if not value:
		return ""
	return cstr(frappe.db.get_value("Fiscal Year", {"year_start_date": ["<=", value], "year_end_date": [">=", value]}, "name", order_by="year_start_date desc"))


def current_year() -> str:
	return fiscal_year_of(clock.now().date())


def get_record(case: str, year: str):
	name = frappe.db.get_value(RECORD, {"contract_case": case, "fiscal_year": year, "kind": ["!=", "Correction"]}, "name")
	return frappe.get_doc(RECORD, name) if name else None


def records_of(case: str) -> list:
	return [frappe.get_doc(RECORD, n) for n in frappe.get_all(RECORD, filters={"contract_case": case, "kind": ["!=", "Correction"]}, pluck="name", order_by="fiscal_year asc")]


def _content(rec) -> dict[str, Any]:
	return {"contract": rec.contract_case, "year": rec.fiscal_year, "charge": cstr(rec.charge), "explanation": cstr(rec.explanation).strip(), "evidence": sorted(records.loads(rec.evidence_json, []))}


def content_digest(rec) -> str:
	return records.digest(_content(rec))


def confirmations(rec) -> list[dict[str, Any]]:
	return records.loads(rec.confirmations_json, [])


def confirmed(rec) -> dict[str, Any] | None:
	"""The latest confirmation, if it is of exactly the content now prepared. A change to the charge, explanation or evidence is unconfirmed until Finance approval confirms it again."""
	found = confirmations(rec)
	return found[-1] if found and found[-1]["content_digest"] == content_digest(rec) else None


def label_of(rec, route: str, *, year_now: str | None = None) -> str:
	"""What the year's funding is, in the words the screens use."""
	if rec.request_state == "Completed":
		return {seam.OUTCOME_ALREADY_COVERED: S_ALREADY, seam.OUTCOME_NO_CHARGE: S_NO_CHARGE}.get(rec.outcome, S_APPROVED)
	if rec.request_state == "Declined":
		return S_DECLINED
	if rec.request_state == "Withdrawn":
		return S_WITHDRAWN
	if rec.request_state == "Open":
		if rec.outcome == seam.OUTCOME_SHORTFALL:
			return S_SHORTFALL
		if rec.outcome == seam.OUTCOME_RETURNED:
			return S_RETURNED
		if cstr(rec.outcome) == seam.SCOPE_REVIEW:
			return S_SCOPE
		return S_PENDING if confirmed(rec) else S_YEAR_REQUIRED
	if confirmed(rec):
		return S_READY
	return S_FUTURE if (year_now and rec.fiscal_year > year_now) else S_YEAR_REQUIRED


def funded_years(case: str) -> set[str]:
	return {r.fiscal_year for r in records_of(case) if r.request_state == "Completed" and r.outcome in COVERED}


# ---- the route ------------------------------------------------------------------------------------------------------------------


def record_route(case: str, *, route: str, authority_name: str, approved_amount: str, evidence: list[str], schedule: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordContractFundingRoute`: the head of procurement records how the contract is funded, with the authority's evidence and the contract's year shares. Registration and evidence capture never wait for
	it, and recording it settles the route for financial work; changing it after any year was funded needs an explicit reconciliation, never a relabel."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		_external(doc)
		if route not in ROUTES:
			invalid({"route": "Choose KenTender Budget or Outside KenTender Budget."})
		refs = [cstr(e).strip() for e in evidence or [] if cstr(e).strip()]
		problems: dict[str, str] = {}
		if not refs:
			problems["evidence"] = "Give the evidence of the funding authority."
		rows, seen = [], set()
		for number, row in enumerate(schedule or [], start=1):
			year = cstr(row.get("year")).strip()
			if not year or not frappe.db.exists("Fiscal Year", year):
				problems[f"schedule.{number}.year"] = "Choose a financial year that exists on this site."
				continue
			if year in seen:
				problems[f"schedule.{number}.year"] = "Each year appears once."
				continue
			seen.add(year)
			try:
				rows.append({"year": year, "amount": _money(row.get("amount"), "the year's share", f"schedule.{number}.amount")})
			except frappe.ValidationError as exc:
				problems.update(getattr(exc, "fields", {}) or {f"schedule.{number}.amount": "Enter the year's share as an amount."})
		if rows and sum(Decimal(r["amount"]) for r in rows) > Decimal(cstr(doc.contract_value or 0)):
			problems["schedule"] = "The year shares come to more than the contract's current value."
		if route == ROUTE_OUTSIDE and not cstr(authority_name).strip():
			problems["authority"] = "Name the responsible authority that approved the funding."
		invalid(problems)
		if doc.funding_route and doc.funding_route != route and funded_years(case):
			fail("CM_RECONCILE", reason="A year of this contract has already been funded. Changing the route needs an explicit reconciliation of the existing Budget coverage; relabelling releases or duplicates nothing.")
		now = str(clock.now())
		authority_record = {"route": route, "authority": cstr(authority_name).strip(), "approved_amount": _money(approved_amount, "the approved amount", "approved_amount") if cstr(approved_amount).strip() else "",
			"evidence": refs, "recorded_by": actor, "recorded_at": now}
		records.bump(doc, funding_route=route, funding_authority_json=records.dumps(authority_record))
		for row in rows:
			rec = get_record(case, row["year"])
			if rec is None:
				records.new(RECORD, contract_case=case, fiscal_year=row["year"], scope_key=seam.scope_key(kind="Initial", contract=case, target_year=row["year"]), kind="Initial", schedule_amount=row["amount"],
					request_state="Not requested", confirmations_json="[]", history_json="[]", evidence_json="[]", record_version=1)
			else:
				records.update(rec, schedule_amount=row["amount"], record_version=cint(rec.record_version) + 1)
		if route == ROUTE_BUDGET:
			work.finish(case, command="RecordContractFundingRoute", actor=actor)
			_open_year_work(doc)
		events.record(case, "Funding route recorded", actor, f"Funding route recorded: {route}.", route=route, years=[r["year"] for r in rows])
		return records.summary(doc, route=route)

	return records.command("RecordContractFundingRoute", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "route": route, "authority": authority_name, "approved": approved_amount, "evidence": list(evidence or []), "schedule": list(schedule or [])}, body=body,
		authorise=lambda: authority.require(actor, work.HOP))


def _open_year_work(doc) -> None:
	"""The Finance work that is the contract's to give: the year's basis, in the opening review. An unconfirmed year that is the current one or earlier asks Finance approval; a later year waits for its turn."""
	now = current_year()
	for rec in records_of(doc.name):
		if rec.request_state in ("Not requested", "Open") and not confirmed(rec) and (not now or rec.fiscal_year <= now):
			work.assign(doc.name, "ConfirmContractFundingEvidence", f"Confirm the funding for {rec.fiscal_year}.", f"year {rec.fiscal_year}", cint(doc.record_version), work.holders("Finance approval"), role="Finance approval")


# ---- Finance: prepare and confirm the year's basis -----------------------------------------------------------------------------------


def prepare_year_basis(case: str, *, year: str, charge: str, explanation: str, evidence: list[str], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`PrepareContractFundingBasis` (Finance preparation): assemble the year's reconciliation from the schedule and the accounting evidence. Preparing confirms nothing and moves no money; the figures are
	confirmed by Finance approval, who is not the preparer of the same subject."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		_external(doc)
		rec = _year(case, year)
		refs = sorted({cstr(e).strip() for e in evidence or [] if cstr(e).strip()})
		problems: dict[str, str] = {}
		if not cstr(explanation).strip():
			problems["explanation"] = "Explain how the year's charge was reached from the contract's schedule and the accounting evidence."
		if not refs:
			problems["evidence"] = "Give the evidence the charge rests on."
		try:
			amount = _money(charge, "the funding charge", "charge")
		except frappe.ValidationError as exc:
			problems.update(getattr(exc, "fields", {}) or {"charge": "Enter the funding charge as an amount."})
			amount = ""
		invalid(problems)
		records.update(rec, charge=amount, explanation=cstr(explanation).strip(), evidence_json=records.dumps(refs), prepared_by=actor, prepared_at=clock.now(), record_version=cint(rec.record_version) + 1)
		events.record(case, "Funding basis prepared", actor, f"The funding basis for {year} was prepared.", year=year)
		return records.summary(doc, year=year)

	return records.command("PrepareContractFundingBasis", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "year": year, "charge": charge, "explanation": explanation, "evidence": list(evidence or [])}, body=body,
		authorise=lambda: authority.require(actor, "Finance preparation"))


def _year(case: str, year: str):
	rec = get_record(case, year)
	if rec is None:
		fail("CM_CHANGED", reason=f"No funding year {year} is recorded for this contract. The head of procurement records the year shares first.")
	return rec


def basis_of(rec, doc, confirmation: dict[str, Any]) -> dict[str, Any]:
	"""`ContractFundingBasis.v1` for the year: exactly what Finance confirmed, and who. Contract Management owns it; Budget receives it as validated facts and opaque evidence references."""
	intake = records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": rec.contract_case, "state": ["in", ["Draft", "Effective"]]}, "intake_json", order_by="version_no desc"), {})
	return {"schema": seam.BASIS_SCHEMA, "contract": rec.contract_case, "intake_revision": cint(intake.get("revision") or doc.intake_revision), "agreement_version": cint(doc.current_agreement),
		"confirmation": {"id": f"{rec.name}-C{confirmation['revision']}", "revision": confirmation["revision"]}, "target_year": rec.fiscal_year, "currency": cstr(doc.currency) or "KES", "scale": 2,
		"confirmed_charge": confirmation["charge"], "explanation": confirmation["explanation"], "evidence": confirmation["evidence"], "confirmers": [{"user": confirmation["by"], "assignment": confirmation["assignment"], "at": confirmation["at"]}],
		"digest": confirmation["basis_digest"], "unsupported_residual": []}


def _confirm_year(doc, rec, *, charge: str, explanation: str, evidence: list[str] | None, actor: str, idempotency_key: str) -> dict[str, Any]:
	"""Append Finance approval's confirmation of one year's basis to a locked contract. Shared by the stand-alone command and by `ConfirmOpeningPosition`, which confirms the prepared basis in the same action."""
	case, year = doc.name, rec.fiscal_year
	route = cstr(doc.funding_route)
	if not route:
		fail("CM_CHANGED", reason="The head of procurement has not recorded how this contract is funded.")
	if cstr(charge).strip() or cstr(explanation).strip() or evidence:
		amount = _money(charge or rec.charge, "the funding charge", "charge")
		text = cstr(explanation or rec.explanation).strip()
		refs = sorted({cstr(e).strip() for e in (evidence or records.loads(rec.evidence_json, [])) if cstr(e).strip()})
		records.update(rec, charge=amount, explanation=text, evidence_json=records.dumps(refs))
		rec = frappe.get_doc(RECORD, rec.name)
	if not cstr(rec.charge) or not cstr(rec.explanation).strip() or not records.loads(rec.evidence_json, []):
		invalid({"charge": "The funding charge, its explanation and its evidence are needed before they can be confirmed."})
	segregation.preparer_not_decider(actor, [rec.prepared_by] if rec.prepared_by else [], what="the funding basis")
	if confirmed(rec):
		return records.summary(doc, year=year, already="confirmed")
	revision = len(confirmations(rec)) + 1
	assignment = people.decision(actor, "Finance approval")
	confirmation = {"revision": revision, "by": actor, "assignment": cstr(getattr(assignment, "assignment_id", "") or ""), "at": str(clock.now()), "charge": rec.charge, "explanation": cstr(rec.explanation).strip(),
		"evidence": sorted(records.loads(rec.evidence_json, [])), "content_digest": content_digest(rec)}
	confirmation["basis_digest"] = records.digest({**confirmation, "contract": case, "year": year, "currency": cstr(doc.currency) or "KES"})
	records.append_json(rec, "confirmations_json", confirmation)
	records.update(rec, basis_digest=confirmation["basis_digest"], record_version=cint(rec.record_version) + 1)
	rec = frappe.get_doc(RECORD, rec.name)
	work.finish(case, command="ConfirmContractFundingEvidence", subject=f"year {year}", actor=actor)
	if route == ROUTE_BUDGET:
		if rec.request_state == "Open":
			_send_basis(doc, rec, confirmation, idempotency_key)
		else:
			work.assign(case, "RequestExistingContractFunding", f"Request funding for {year}.", f"year {year}", cint(doc.record_version), work.holders(work.HOP), role=work.HOP)
	events.record(case, "Funding basis confirmed", actor, f"The funding basis for {year} was confirmed by Finance.", year=year, revision=revision, digest=confirmation["basis_digest"])
	return records.summary(doc, year=year, revision=revision)


def confirm_with_opening(doc, actor: str, idempotency_key: str) -> list[str]:
	"""`ConfirmOpeningPosition` also confirms the funding basis (CM-CHG-001 v0.10 section 20.6): each year up to the current one whose basis Finance preparation has already prepared, unless the confirming person prepared it
	(then it stays for another approver). Returns the years confirmed. Nothing is invented: a year with no prepared basis is left for the stand-alone confirmation."""
	if doc.source_kind != "External record" or cstr(doc.funding_route) != ROUTE_BUDGET:
		return []
	now, done = current_year(), []
	for rec in records_of(doc.name):
		prepared = cstr(rec.charge) and cstr(rec.explanation).strip() and records.loads(rec.evidence_json, [])
		if confirmed(rec) or not prepared or (now and rec.fiscal_year > now) or cstr(rec.prepared_by).lower() == actor.lower():
			continue
		_confirm_year(doc, rec, charge="", explanation="", evidence=None, actor=actor, idempotency_key=f"{idempotency_key}:{rec.fiscal_year}")
		done.append(rec.fiscal_year)
	return done


def confirm_funding_evidence(case: str, *, year: str, charge: str = "", explanation: str = "", evidence: list[str] | None = None, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ConfirmContractFundingEvidence` (Finance approval): confirm the exact target-year funding basis, in the opening review. Appends a versioned confirmation and never rewrites an earlier one or the contract's
	opening position. The preparer of the same figures cannot confirm them. If a request is open for the year Budget is told of the new basis; if not, the head is asked to raise it."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		_external(doc)
		return _confirm_year(doc, _year(case, year), charge=charge, explanation=explanation, evidence=evidence, actor=actor, idempotency_key=idempotency_key)

	return records.command("ConfirmContractFundingEvidence", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "year": year, "charge": charge, "explanation": explanation, "evidence": list(evidence or [])}, body=body,
		authorise=lambda: authority.require(actor, "Finance approval"))


def _send_basis(doc, rec, confirmation: dict[str, Any], key: str) -> None:
	"""A later confirmation refreshes the same Budget request by a versioned owner event (the old one is not deleted); Budget returns an entry already submitted for refreshed preparation."""
	try:
		seam.update_basis(f"{rec.name}:basis:{confirmation['revision']}", scope_key=rec.scope_key, basis=basis_of(rec, doc, confirmation), evidence=confirmation["evidence"])
	except (seam.Unavailable, seam.Refused) as exc:
		fail("CM_FUNDING", reason=cstr(exc) or "The funding owner did not accept the funding basis.", year=rec.fiscal_year)


# ---- the request ----------------------------------------------------------------------------------------------------------------


def request_funding(case: str, *, year: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RequestExistingContractFunding`: the head raises the one request for the contract and this year (Initial for the first funded year, Annual for a later one). An incomplete Finance basis does not
	prevent it: the request is received and shows **Year allocation required** with Finance's task. Contract Management creates no commitment and no reservation."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		_external(doc)
		rec = _year(case, year)
		if cstr(doc.funding_route) != ROUTE_BUDGET:
			fail("CM_CHANGED", reason="Only a contract funded through KenTender Budget raises a funding request.")
		if rec.request_state in ("Open", "Completed"):
			return records.summary(doc, year=year, already=rec.request_state.lower())
		status = None
		try:
			status = seam.year_status(year)
		except Exception:
			status = None
		other = [r for r in records_of(case) if r.name != rec.name and r.request_state in ("Open", "Completed")]
		kind = "Annual" if other else "Initial"
		last = confirmations(rec)[-1] if confirmations(rec) and confirmed(rec) else None
		request = {"kind": kind, "contract": case, "contract_reference": cstr(doc.contract_id), "agreement_version": cstr(doc.current_agreement), "supplier_name": cstr(doc.supplier_name), "target_year": year,
			"currency": cstr(doc.currency) or "KES", "source_organisation_unit": cstr(doc.managing_unit), "basis": basis_of(rec, doc, last) if last else {}, "evidence": records.loads(rec.evidence_json, [])}
		records.update(rec, kind=kind, request_state="Open", outcome="", record_version=cint(rec.record_version) + 1)
		try:
			answer = seam.receive(f"{rec.name}:request:{idempotency_key}", request)
		except seam.Refused as exc:
			fail("CM_FUNDING", reason=cstr(exc), year=year)
		except seam.Unavailable as exc:
			fail("CM_FUNDING", reason=cstr(exc), year=year)
		rec = frappe.get_doc(RECORD, rec.name)
		scope = (answer.get("request") or {}).get("scope_key") or rec.scope_key
		fields = {"request_reference": cstr((answer.get("request") or {}).get("code")), "scope_key": scope}
		if rec.request_state == "Open" and answer.get("closed"):
			fields.update(request_state="Completed", outcome=cstr(answer["closed"]))  # Budget closed it at once (already covered, or no charge) and the outcome has arrived in order
		records.update(rec, **fields)
		rec = frappe.get_doc(RECORD, rec.name)
		work.finish(case, command="RequestExistingContractFunding", subject=f"year {year}", actor=actor)
		_waiting(doc, rec)
		events.record(case, "Funding requested", actor, f"Funding for {year} was requested from Budget ({kind}).", year=year, kind=kind, request=rec.request_reference, budget_year_active=bool(status and status.get("active")))
		return records.summary(doc, year=year, kind=kind, request=rec.request_reference)

	return records.command("RequestExistingContractFunding", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "year": year}, body=body,
		authorise=lambda: authority.require(actor, work.HOP))


def _waiting(doc, rec) -> None:
	"""The contract's linked waiting item for the request: Finance's task when the basis is missing, otherwise the head's wait on Budget."""
	if rec.request_state != "Open":
		work.finish(doc.name, command=work.waiting_command("RequestExistingContractFunding", "budget"), subject=f"year {rec.fiscal_year}", actor="")
		return
	if confirmed(rec):
		work.assign(doc.name, work.waiting_command("RequestExistingContractFunding", "budget"), "Waiting for Budget to fund this contract.", f"year {rec.fiscal_year}", cint(doc.record_version), work.holders(work.HOP), role=work.HOP, state="Waiting")
	else:
		work.assign(doc.name, "ConfirmContractFundingEvidence", f"Confirm the funding for {rec.fiscal_year}.", f"year {rec.fiscal_year}", cint(doc.record_version), work.holders("Finance approval"), role="Finance approval")
		work.assign(doc.name, work.waiting_command("RequestExistingContractFunding", "finance"), "Waiting for Finance to confirm the funding year.", f"year {rec.fiscal_year}", cint(doc.record_version), work.holders(work.HOP), role=work.HOP, state="Waiting")


def withdraw_funding_request(case: str, *, year: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`WithdrawContractFundingRequest`: Contract Management alone withdraws an open request before funding. Unapproved preparation in Budget is abandoned; no commitment changes."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		rec = _year(case, year)
		if rec.request_state != "Open":
			fail("CM_CHANGED", reason="There is no open funding request for this year.")
		text = cstr(reason).strip()
		if len(text) < 10:
			invalid({"reason": "Give the reason in at least 10 characters."})
		try:
			seam.withdraw(f"{rec.name}:withdraw:{idempotency_key}", scope_key=rec.scope_key, reason=text)
		except (seam.Refused, seam.Unavailable) as exc:
			fail("CM_FUNDING", reason=cstr(exc), year=year)
		rec = frappe.get_doc(RECORD, rec.name)
		records.update(rec, request_state="Withdrawn", outcome=seam.OUTCOME_WITHDRAWN, record_version=cint(rec.record_version) + 1)
		_waiting(doc, frappe.get_doc(RECORD, rec.name))
		work.finish(case, command="ConfirmContractFundingEvidence", subject=f"year {year}", state="Superseded", actor=actor)
		events.record(case, "Funding request withdrawn", actor, f"The funding request for {year} was withdrawn.", year=year, reason=text)
		return records.summary(doc, year=year)

	return records.command("WithdrawContractFundingRequest", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "year": year, "reason": reason}, body=body,
		authorise=lambda: authority.require(actor, work.HOP))


def request_funding_correction(case: str, *, commitment: str, correction_reference: str, reason: str, evidence: list[str], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RequestContractFundingCorrection`: the head asks Budget to correct a Closed commitment, citing the exact commitment, the Contract Management record that shows the error and the evidence. Contract Management
	never adjusts a Closed commitment; Budget's Officer and a different Approver decide. A Budget Officer may start the same correction without this request."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		_external(doc)
		text, refs = cstr(reason).strip(), [cstr(e).strip() for e in evidence or [] if cstr(e).strip()]
		problems = {}
		if not cstr(commitment).strip():
			problems["commitment"] = "Name the Closed commitment."
		if not cstr(correction_reference).strip():
			problems["correction_reference"] = "Name the Contract Management record that shows the error."
		if len(text) < 10:
			problems["reason"] = "Give the reason in at least 10 characters."
		if not refs:
			problems["evidence"] = "Give the evidence of the error."
		invalid(problems)
		scope = seam.scope_key(kind="Correction", contract=case, subject_event=cstr(correction_reference).strip())
		rec = frappe.db.get_value(RECORD, {"scope_key": scope}, "name")
		if not rec:
			rec = records.new(RECORD, contract_case=case, fiscal_year=current_year() or fiscal_year_of(clock.now().date()) or "", scope_key=scope, kind="Correction", subject_event=cstr(correction_reference).strip(),
				original_commitment=cstr(commitment).strip(), request_state="Open", explanation=text, evidence_json=records.dumps(refs), confirmations_json="[]", history_json="[]", record_version=1).name
		try:
			answer = seam.receive(f"{rec}:correction:{idempotency_key}", {"kind": "Correction", "contract": case, "contract_reference": cstr(doc.contract_id), "supplier_name": cstr(doc.supplier_name), "currency": cstr(doc.currency) or "KES",
				"subject_event": cstr(correction_reference).strip(), "original_commitment": cstr(commitment).strip(), "evidence": refs})
		except (seam.Refused, seam.Unavailable) as exc:
			fail("CM_FUNDING", reason=cstr(exc))
		records.update(frappe.get_doc(RECORD, rec), request_reference=cstr((answer.get("request") or {}).get("code")))
		events.record(case, "Funding correction requested", actor, "A correction of a Closed commitment was requested from Budget.", commitment=cstr(commitment), reference=cstr(correction_reference))
		return records.summary(doc)

	return records.command("RequestContractFundingCorrection", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "commitment": commitment, "reference": correction_reference, "reason": reason, "evidence": list(evidence or [])}, body=body, authorise=lambda: authority.require(actor, work.HOP))


# ---- Budget's outcomes -------------------------------------------------------------------------------------------------------------


def receive_outcome(outcome: dict[str, Any]) -> dict[str, Any] | None:
	"""`ReceiveContractFundingOutcome` (service only, ordered and idempotent): record what Budget decided. An outcome already received, or older than one received, changes nothing and is acknowledged again; a
	later one closes or reopens the contract's waiting work. Nothing here funds anything."""
	scope = cstr(outcome.get("scope_key"))
	name = frappe.db.get_value(RECORD, {"scope_key": scope}, "name")
	if not name:
		return None  # a request this site's Contract Management does not hold: not acknowledged, so the owner keeps it
	rec = frappe.get_doc(RECORD, name, for_update=True)
	sequence = cint(outcome.get("sequence"))
	if sequence <= cint(rec.last_outcome_sequence):
		return {"receipt": f"{rec.name}:{sequence}", "repeated": True}
	doc = frappe.get_doc(CASE, rec.contract_case)
	state, name_of = rec.request_state, cstr(outcome.get("outcome"))
	fields: dict[str, Any] = {"last_outcome_sequence": sequence, "outcome": name_of, "record_version": cint(rec.record_version) + 1}
	if name_of in seam.CLOSING:
		fields["request_state"] = {seam.OUTCOME_APPROVED: "Completed", seam.OUTCOME_ALREADY_COVERED: "Completed", seam.OUTCOME_NO_CHARGE: "Completed", seam.OUTCOME_DECLINED: "Declined", seam.OUTCOME_WITHDRAWN: "Withdrawn"}[name_of]
	elif state in ("Declined", "Withdrawn", "Not requested"):
		fields["request_state"] = "Open"
	records.update(rec, **fields)
	records.append_json(rec, "history_json", {"at": str(clock.now()), "sequence": sequence, "outcome": name_of, "detail": outcome.get("detail") or {}})
	rec = frappe.get_doc(RECORD, name)
	_waiting(doc, rec)
	if rec.request_state == "Completed":
		work.finish(doc.name, command="RequestExistingContractFunding", subject=f"year {rec.fiscal_year}", actor="")
	events.record(doc.name, "Funding outcome received", "Budget", f"Budget reported for {rec.fiscal_year}: {name_of}.", year=rec.fiscal_year, outcome=name_of, sequence=sequence)
	return {"receipt": f"{rec.name}:{sequence}"}


class OutcomeReceiver:
	def receive_outcome(self, *, outcome: dict[str, Any]) -> dict[str, Any] | None:
		with records.atomic():
			return receive_outcome(outcome)

	def waiting_item(self, *, scope_key: str) -> dict[str, Any] | None:
		"""Contract Management's own waiting item for a request that waits on Finance: who holds it and what they open. Budget shows it and stores none of it."""
		name = frappe.db.get_value(RECORD, {"scope_key": scope_key}, "name")
		if not name:
			return None
		rec = frappe.get_doc(RECORD, name)
		if confirmed(rec) or rec.request_state != "Open":
			return None
		holder = next(iter(work.holders("Finance approval")), "")
		return {"holder": people.full_name(holder) if holder else "", "responsibility": "Finance approval", "action": "Open contract review", "contract": rec.contract_case}


def receiver() -> OutcomeReceiver:
	return OutcomeReceiver()


# ---- what the funding holds ---------------------------------------------------------------------------------------------------------


@holds.provider("funding")
def _funding_holds(case: str):
	"""The affected unfunded scope (CM-CHG-001 v0.10 section 20.5). Only a contract whose route has been recorded is judged; one still waiting for its route keeps its earlier behaviour until the head records it."""
	route = cstr(frappe.db.get_value(CASE, case, "funding_route"))
	if not route or frappe.db.get_value(CASE, case, "source_kind") != "External record":
		return
	if route == ROUTE_OUTSIDE:
		if not outside_confirmed(case):
			yield holds.Hold(key=f"funding:{case}:outside", kind="Funding", reason="Funding is not confirmed for this contract.", blocks=FUNDING_HOLD_BLOCKS, owner="Head of procurement function and Finance approval",
				clearing="The head of procurement confirms the funding authority's evidence and Finance approval confirms the same in the opening review")
		return
	covered, now = funded_years(case), current_year()
	if now and now not in covered:
		yield holds.Hold(key=f"funding:{case}:spending", kind="Funding", reason=f"Funding for {now} is not confirmed, so new spending and increases wait.", blocks=frozenset({"new_spending", "vary_contract"}), owner="Budget Officer",
			clearing=f"Budget funds the confirmed charge for {now}, or confirms that Budget already covers it")
	unpaid: dict[str, list[str]] = {}
	for invoice in frappe.get_all("Contract Invoice", filters={"contract_case": case}, fields=["invoice_no", "invoice_date"]):
		year = fiscal_year_of(invoice.invoice_date) or now
		if year and year not in covered:
			unpaid.setdefault(year, []).append(f"invoice {invoice.invoice_no}")
	for advance in frappe.get_all("Contract Advance", filters={"contract_case": case}, pluck="advance_no"):
		if now and now not in covered:
			unpaid.setdefault(now, []).append(f"advance {advance}")
	if now and now not in covered:
		unpaid.setdefault(now, [])  # an advance paid before any invoice or advance record exists belongs to the current year, so that year holds even when nothing is recorded against it yet
	for year, subjects in sorted(unpaid.items()):
		yield holds.Hold(key=f"funding:{case}:pay:{year}", kind="Funding", reason="Funding is not confirmed for this payment.", blocks=frozenset({"pay"}), owner="Budget Officer",
			clearing=f"Budget funds the confirmed charge for {year}", scope=tuple(subjects) or ("advance",))


def advance_hold(case: str):
	"""The funding hold an advance (a payment before any invoice) meets: an advance belongs to the current year's funding. None when it is covered or the contract's route is not yet recorded."""
	for hold in holds.blocking(case, "pay", None):
		if hold.kind == "Funding" and (hold.key.endswith(":outside") or hold.key.endswith(f":pay:{current_year()}")):
			return hold
	return None


def case_of_order(order: str) -> str:
	"""The contract an order belongs to, by the identity Contract Management stamped on it."""
	identity = frappe.db.get_value("Purchase Order", order, "cm_operation_identity")
	return cstr(frappe.db.get_value("Contract Operation Intent", {"operation_identity": identity}, "contract_case")) if identity else ""


def recheck(case: str, subject: str | None, *, consequence: str = "pay") -> None:
	"""A payment, advance or settlement posts only for a scope whose funding is confirmed (CM-CHG-001 v0.10 section 20.5). Read fresh from the holds framework at the moment of the native posting, so a hold that arose
	after Contract Management drew its button still stops the posting, through every native route. Factual recording is not a posting and is never stopped here. Raises `CM_HOLD` with the reason, the holder and what clears it."""
	if not case:
		return
	if subject:
		blocking = [h for h in holds.blocking(case, consequence, subject) if h.kind == "Funding"]
	else:
		advance = advance_hold(case)
		blocking = [advance] if advance else []
	if blocking:
		fail("CM_HOLD", reason=blocking[0].reason, consequence=consequence, holder=blocking[0].owner, clears_with=blocking[0].clearing, scope=list(blocking[0].scope))


def outside_confirmed(case: str) -> bool:
	"""Route B: the head's evidence is recorded and Finance approval has confirmed the funded scope in the opening review."""
	doc = frappe.get_doc(CASE, case)
	authority_record = records.loads(doc.funding_authority_json, {})
	if not authority_record.get("evidence"):
		return False
	return any(confirmed(rec) for rec in records_of(case))


def case_of_native_invoice(native_invoice: str) -> tuple[str, str] | None:
	"""The contract and invoice subject a native Purchase Invoice belongs to, for the native payment guard."""
	row = frappe.db.get_value("Contract Invoice", {"native_invoice": native_invoice}, ["contract_case", "invoice_no"], as_dict=True)
	return (row.contract_case, f"invoice {row.invoice_no}") if row else None


def view(case: str, actor: str = "") -> dict[str, Any]:
	"""The funding section of the contract for its boards: the route, the label, each year's position and who holds the next step. Reads Contract Management's own records only."""
	doc = frappe.get_doc(CASE, case)
	route = cstr(doc.funding_route)
	if doc.source_kind != "External record":
		return {"applies": False}
	now = current_year()
	years = []
	for rec in records_of(case):
		last = confirmations(rec)[-1] if confirmations(rec) else None
		years.append({"year": rec.fiscal_year, "label": label_of(rec, route, year_now=now), "schedule_amount": cstr(rec.schedule_amount), "charge": cstr(rec.charge), "confirmed": bool(confirmed(rec)), "request_state": rec.request_state,
			"outcome": cstr(rec.outcome), "request": cstr(rec.request_reference), "prepared_by": cstr(rec.prepared_by), "confirmed_by": cstr(last["by"]) if last and confirmed(rec) else "", "revision": len(confirmations(rec)),
			"current": rec.fiscal_year == now})
	label = S_NOT_LINKED if not route else (S_OUTSIDE if route == ROUTE_OUTSIDE and outside_confirmed(case) else S_NOT_CONFIRMED if route == ROUTE_OUTSIDE else "")
	return {"applies": True, "route": route, "label": label, "authority": records.loads(doc.funding_authority_json, {}), "years": years, "held": [h.reason for h in holds.open_holds(case) if h.kind == "Funding"]}
