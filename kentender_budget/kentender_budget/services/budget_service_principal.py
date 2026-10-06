# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD v1.12 §7 / BUD-BR-015 — how an in-process downstream module proves
which service principal it is (AUD-XC-002, AUD-BUD-012).

The money-moving Budget functions (`check_funding`, `reserve_funding`,
`release_reservation`, `convert_reservation`, `adjust_commitment`,
`revalidate_reservations`) are in-process service calls made by a named
downstream service, never web endpoints. Budget authenticates the *principal*
the calling service passes, not the session's role: every function takes a
`ServiceCaller` and checks it against the fixed allow-list of
(principal, action) pairs below.

A `ServiceCaller` is a Python object that only this module can mint, so it
cannot arrive in a web request (JSON cannot construct one) and a human
session without it is refused with `BUDGET_DOWNSTREAM_FORBIDDEN`. The mint
function is called only from the owning module's gateway; a repository test
(`test_budget_service_principal.py`) fails if any other file mints a
principal.

Owner decision 6 Oct 2026:
- Procurement Requisitions releases only the exact reservations its own
  requisition created, together with the Planning drawdown reversal.
- Contract Management converts reservations to commitments, releases an
  unused reservation amount on an authenticated owner event, and adjusts a
  commitment. (No Contract Management module exists yet; the principal is a
  registered capability exercised by tests.)
- Planning, Tenders, Evaluation and Award can do none of it.
"""

from __future__ import annotations

import frappe
from frappe import _

PRINCIPAL_REQUISITIONS = "procurement_requisitions"
PRINCIPAL_CONTRACT = "contract_management"
# Budget's own housekeeping (revalidation after a Budget Version change).
PRINCIPAL_BUDGET = "budget_internal"
# Registered, but holding no money-moving permission at all.
PRINCIPAL_PLANNING = "procurement_planning"
PRINCIPAL_TENDERS = "tenders"
PRINCIPAL_EVALUATION = "evaluation"
PRINCIPAL_AWARD = "award"

ACTION_CHECK = "check_funding"
ACTION_RESERVE = "reserve_funding"
ACTION_RELEASE = "release_reservation"
ACTION_CONVERT = "convert_reservation"
ACTION_ADJUST = "adjust_commitment"
ACTION_REVALIDATE = "revalidate_reservations"

ALLOWED_ACTIONS: dict[str, frozenset[str]] = {
	PRINCIPAL_REQUISITIONS: frozenset({ACTION_CHECK, ACTION_RESERVE, ACTION_RELEASE}),
	PRINCIPAL_CONTRACT: frozenset({ACTION_CONVERT, ACTION_RELEASE, ACTION_ADJUST}),
	PRINCIPAL_BUDGET: frozenset({ACTION_REVALIDATE}),
	PRINCIPAL_PLANNING: frozenset(),
	PRINCIPAL_TENDERS: frozenset(),
	PRINCIPAL_EVALUATION: frozenset(),
	PRINCIPAL_AWARD: frozenset(),
}

# The label recorded on the funding ledger and on a reservation's `calling_module`.
PRINCIPAL_LABEL: dict[str, str] = {
	PRINCIPAL_REQUISITIONS: "Procurement Requisitions",
	PRINCIPAL_CONTRACT: "Contract Management",
	PRINCIPAL_BUDGET: "Budget & Funding",
	PRINCIPAL_PLANNING: "Procurement Planning",
	PRINCIPAL_TENDERS: "Tenders",
	PRINCIPAL_EVALUATION: "Evaluation",
	PRINCIPAL_AWARD: "Award",
}

_MINT = object()


class ServiceCaller:
	"""An authenticated downstream service principal. Immutable; mint it with
	`service_caller()`. `reference` names what the principal acts for: the
	requisition reference for Requisitions, the contract for Contract
	Management."""

	__slots__ = ("principal", "reference")

	def __init__(self, principal: str, reference: str, _token: object = None):
		if _token is not _MINT:
			raise TypeError("A ServiceCaller can only be created with service_caller()")
		object.__setattr__(self, "principal", principal)
		object.__setattr__(self, "reference", reference)

	def __setattr__(self, name, value):
		raise AttributeError("ServiceCaller is immutable")

	def __repr__(self) -> str:
		return f"ServiceCaller({self.principal!r}, {self.reference!r})"


def service_caller(principal: str, *, reference: str = "") -> ServiceCaller:
	if principal not in ALLOWED_ACTIONS:
		raise ValueError(f"Unknown Budget service principal: {principal!r}")
	return ServiceCaller(principal, (reference or "").strip(), _MINT)


def refuse(message: str) -> None:
	frappe.throw(message, frappe.PermissionError, title="BUDGET_DOWNSTREAM_FORBIDDEN")


def require_principal(caller, action: str) -> ServiceCaller:
	"""Refuse unless `caller` is a minted `ServiceCaller` whose principal is
	allowed `action`. Returns the caller."""
	if not isinstance(caller, ServiceCaller):
		refuse(_("This Budget action can only be called by the owning downstream service."))
	if action not in ALLOWED_ACTIONS.get(caller.principal, frozenset()):
		refuse(_("{0} may not call {1}.").format(caller.principal, action))
	return caller
