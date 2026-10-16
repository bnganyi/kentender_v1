# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published seam for a contract's funding request (BUD-CHG-001 v1.16 sections 8.6, 8.7; CM-CHG-001 v0.10 sections 20.4, 20.4A, 20.6).

Contract Management raises one funding request for an independently registered contract (an Initial or Annual request for a target Budget year, an Additional request for an exact increment, or a
Correction request for a Closed commitment). The funding owner (Budget) holds the request, its entry and its decision; Contract Management holds the contract, the opening review and the Finance work,
and sends Budget validated funding facts and opaque evidence references only. Neither imports the other: each registers on a hook.

**Requests, Contract Management to the funding owner.** The owner registers `kt_contract_funding_request_owner`, a callable returning an object (or None to decline) with:

    receive(*, identity, request)               -> {"request", "status", "created", ...}   one request per scope; an identical replay returns the original
    update_basis(*, identity, scope_key, basis, evidence) -> {...}   later source evidence for the same request; changed submitted evidence returns the entry for resubmission
    withdraw(*, identity, scope_key, reason)    -> {...}   Contract Management alone, before funding; changes no commitment
    lookup(*, scope_key)                        -> summary | None
    year_status(*, fiscal_year)                 -> {"fiscal_year", "active", "currency"} | None   (optional; is there an Active Budget for the year)

`request` carries: `kind`, `contract`, `contract_reference`, `agreement_version`, `supplier_name`, `target_year`, `currency`, `source_organisation_unit`, `subject_event`, `original_commitment`, `basis`
(a `ContractFundingBasis.v1`, or empty while Finance has not confirmed the year), `evidence` (opaque references). `scope_key(...)` below builds the identity that makes a request unique.

**Outcomes, the funding owner to Contract Management.** Contract Management registers `kt_contract_funding_outcome_receiver`, a callable returning an object with `receive_outcome(*, outcome)`, where `outcome` is
`{"request", "scope_key", "sequence", "attempt", "outcome", "detail"}`. Outcomes are ordered per request and idempotent on `attempt`; the owner keeps an outbox and retries what is not acknowledged.

**ContractFundingBasis.v1.** Owned and published by Contract Management: the exact contract, intake and agreement revision, the confirmation identity and revision, the target year, currency and precision, the
confirmed gross funding-control charge, its basis and evidence references, the confirmers (user, assignment, time), a digest, and any unsupported residual scope. `validate_basis` checks its shape and
returns a list of problems; it reads no record.

With no owner installed `receive` raises `Unavailable` and the caller treats the request as not made. Tests may set `frappe.flags.kt_contract_funding_request_owners` and `frappe.flags.kt_contract_funding_outcome_receivers`."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

import frappe

OWNER_HOOK = "kt_contract_funding_request_owner"
OWNER_FLAG = "kt_contract_funding_request_owners"
RECEIVER_HOOK = "kt_contract_funding_outcome_receiver"
RECEIVER_FLAG = "kt_contract_funding_outcome_receivers"

KINDS = ("Initial", "Annual", "Additional", "Correction")
BASIS_SCHEMA = "ContractFundingBasis.v1"
YEAR_REQUIRED = "Year allocation required"
YEAR_CONFIRMED = "Confirmed"
SCOPE_REVIEW = "Scope review required"

# What a decision attempt can publish (BUD-CHG-001 v1.16 8.6/8.7): the request stays open after Returned and Funding shortfall; the others close it.
OUTCOME_ENTRY_SUBMITTED = "Funding entry pending"
OUTCOME_RETURNED = "Returned for correction"
OUTCOME_SHORTFALL = "Funding shortfall"
OUTCOME_APPROVED = "Funding entry approved"
OUTCOME_ALREADY_COVERED = "Already covered"
OUTCOME_NO_CHARGE = "No charge to this year"
OUTCOME_DECLINED = "Declined"
OUTCOME_WITHDRAWN = "Withdrawn"
OUTCOME_BASIS_CHANGED = "Basis changed"
# A correction of a Closed commitment (BUD-CHG-001 v1.16 4.11): Budget's Officer records it, a different Approver decides it. An approval closes the request; a return leaves it open for a corrected record.
OUTCOME_CORRECTION_APPROVED = "Correction approved"
OUTCOME_CORRECTION_RETURNED = "Correction returned"
CLOSING = (OUTCOME_APPROVED, OUTCOME_ALREADY_COVERED, OUTCOME_NO_CHARGE, OUTCOME_DECLINED, OUTCOME_WITHDRAWN, OUTCOME_CORRECTION_APPROVED)


class Unavailable(Exception):
	"""No funding owner answered."""


class Refused(Exception):
	"""The funding owner definitively refused the call: nothing was created, and a corrected request may be made."""


def scope_key(*, kind: str, contract: str, target_year: str = "", subject_event: str = "") -> str:
	"""The identity that makes a request unique (BUD v1.16 8.7): Initial and Annual share one identity per contract and target year; an Additional request is unique by its exact increment event and year;
	a Correction request by its exact subject."""
	if kind in ("Initial", "Annual"):
		return f"{contract}|YEAR|{target_year}"
	if kind == "Additional":
		return f"{contract}|ADD|{subject_event}|{target_year}"
	return f"{contract}|COR|{subject_event}"


def owners() -> list[Any]:
	override = frappe.flags.get(OWNER_FLAG)
	if override is not None:
		return list(override)
	found = []
	for path in frappe.get_hooks(OWNER_HOOK) or []:
		try:
			provider = frappe.get_attr(path)()
		except Exception:
			frappe.log_error(title=f"Contract funding request owner failed to load: {path}")
			continue
		if provider is not None:
			found.append(provider)
	return found


def receivers() -> list[Any]:
	override = frappe.flags.get(RECEIVER_FLAG)
	if override is not None:
		return list(override)
	found = []
	for path in frappe.get_hooks(RECEIVER_HOOK) or []:
		try:
			receiver = frappe.get_attr(path)()
		except Exception:
			frappe.log_error(title=f"Contract funding outcome receiver failed to load: {path}")
			continue
		if receiver is not None:
			found.append(receiver)
	return found


def _owner() -> Any:
	chosen = owners()
	if not chosen:
		raise Unavailable("No funding owner is installed on this site.")
	return chosen[-1]


def receive(identity: str, request: dict[str, Any]) -> dict[str, Any]:
	return _owner().receive(identity=identity, request=request)


def update_basis(identity: str, *, scope_key: str, basis: dict[str, Any], evidence: list[str]) -> dict[str, Any]:
	return _owner().update_basis(identity=identity, scope_key=scope_key, basis=basis, evidence=evidence)


def withdraw(identity: str, *, scope_key: str, reason: str) -> dict[str, Any]:
	return _owner().withdraw(identity=identity, scope_key=scope_key, reason=reason)


def lookup(scope_key: str) -> dict[str, Any] | None:
	for owner in owners():
		answer = owner.lookup(scope_key=scope_key)
		if answer is not None:
			return answer
	return None


def year_status(fiscal_year: str) -> dict[str, Any] | None:
	"""Does the funding owner have an Active Budget for this year? `{"fiscal_year", "active", "currency"}`, or None when no owner answers. Contract Management uses it to offer **Request annual funding** only when the year is
	eligible; a calendar date alone grants no funding."""
	for owner in owners():
		reader = getattr(owner, "year_status", None)
		if callable(reader):
			answer = reader(fiscal_year=fiscal_year)
			if answer is not None:
				return answer
	return None


def deliver_outcome(outcome: dict[str, Any]) -> dict[str, Any] | None:
	"""Offer one outcome to the receivers in turn; the first acknowledgement wins. None when nobody acknowledged it (the owner keeps it and retries)."""
	for receiver in receivers():
		receipt = receiver.receive_outcome(outcome=outcome)
		if receipt:
			return receipt
	return None


_MONEY = re.compile(r"^-?\d+(\.\d+)?$")


def validate_basis(basis: Any, *, contract: str, target_year: str, currency: str) -> list[str]:
	"""The problems with a funding basis, in plain words; empty when it can be relied on. It reads no record."""
	if not isinstance(basis, dict) or not basis:
		return ["There is no funding basis."]
	problems = []
	if basis.get("schema") != BASIS_SCHEMA:
		problems.append("The funding basis is not a ContractFundingBasis.v1.")
	if str(basis.get("contract") or "") != contract:
		problems.append("The funding basis is for a different contract.")
	if str(basis.get("target_year") or "") != target_year:
		problems.append("The funding basis is for a different Budget year.")
	if str(basis.get("currency") or "") != currency:
		problems.append("The funding basis is in a different currency.")
	charge = str(basis.get("confirmed_charge") if basis.get("confirmed_charge") is not None else "")
	if not _MONEY.match(charge) or Decimal(charge) < 0:
		problems.append("The confirmed funding charge is not an exact amount of zero or more.")
	if not str(basis.get("digest") or ""):
		problems.append("The funding basis carries no digest.")
	if not (basis.get("evidence") or []):
		problems.append("The funding basis carries no evidence reference.")
	confirmers = basis.get("confirmers") or []
	if not confirmers or any(not str(c.get("user") or "").strip() or not str(c.get("at") or "").strip() for c in confirmers):
		problems.append("The funding basis does not show who confirmed it, and when.")
	if not str(basis.get("explanation") or "").strip():
		problems.append("The funding basis carries no explanation of how the year's charge was reached.")
	return problems
