# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget's side of the contract funding request seam (BUD-CHG-001 v1.16 section 8.6; `kentender_core.services.contract_funding_request_contract`).

Contract Management raises, refreshes and withdraws the funding request of its own contract through the core seam; this is the funding owner's answer. It is the **one gateway** through which that principal
is minted for these actions. A domain refusal (a contract that an Award funded, an unknown Budget year, a request already complete) is a definitive `Refused`; anything else propagates and the caller treats the
outcome as unknown and reads the owner first on its retry (`lookup`)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_budget.services import budget_contract_funding as funding
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller
from kentender_core.services import contract_funding_request_contract as seam


def _guarded(call):
	try:
		answer = call()
	except (frappe.ValidationError, frappe.PermissionError, frappe.DoesNotExistError) as exc:
		raise seam.Refused(frappe.safe_decode(str(exc))) from exc
	if isinstance(answer, dict) and answer.get("ok") is False:
		raise seam.Refused(" ".join(str(m) for m in (answer.get("errors") or {}).values()) or str(answer.get("code") or "Refused"))
	return answer


class Owner:
	def receive(self, *, identity: str, request: dict[str, Any]) -> dict[str, Any]:
		caller = service_caller(PRINCIPAL_CONTRACT, reference=str(request.get("contract") or ""))
		return _guarded(lambda: funding.receive_contract_funding_request(request, identity, caller=caller))

	def update_basis(self, *, identity: str, scope_key: str, basis: dict[str, Any], evidence: list[str]) -> dict[str, Any]:
		contract = scope_key.split("|", 1)[0]
		caller = service_caller(PRINCIPAL_CONTRACT, reference=contract)
		return _guarded(lambda: funding.update_contract_funding_basis(scope_key, basis, evidence, identity, caller=caller))

	def withdraw(self, *, identity: str, scope_key: str, reason: str) -> dict[str, Any]:
		contract = scope_key.split("|", 1)[0]
		caller = service_caller(PRINCIPAL_CONTRACT, reference=contract)
		return _guarded(lambda: funding.withdraw_contract_funding_request(scope_key, reason, identity, caller=caller))

	def year_status(self, *, fiscal_year: str) -> dict[str, Any]:
		budget = funding.target_budget(fiscal_year)
		active = bool(budget and frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name"))
		return {"fiscal_year": fiscal_year, "active": active, "currency": frappe.db.get_value("Procurement Budget", budget, "currency") if budget else ""}

	def lookup(self, *, scope_key: str) -> dict[str, Any] | None:
		name = frappe.db.get_value(funding.REQUEST, {"scope_key": scope_key}, "name")
		return funding.summary(frappe.get_doc(funding.REQUEST, name)) if name else None


def service() -> Owner:
	return Owner()
