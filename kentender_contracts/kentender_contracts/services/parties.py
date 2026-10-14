# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The supplier's people, asked of Supplier Accounts through its published seam (`supplier_account_contract`), never by reading its tables (CM-CHG-001 v0.8 sections 3.1, 6.1).

Authority is read at the moment of the action. With no supplier-accounts provider the answer is **nobody**, so a supplier action fails closed (a Contract Management-only site
registers no supplier signatory, and a bid-submission power is never reused as contract authority: signing needs a current Authorised Signatory, a claim a current Supplier
Representative or Authorised Signatory)."""

from __future__ import annotations

from kentender_core.services import supplier_account_contract


def _rows(function: str, organisation: str, at=None) -> list[dict]:
	provider = supplier_account_contract.provider()
	if provider is None or not organisation or not callable(getattr(provider, function, None)):
		return []
	return list(getattr(provider, function)(organisation_id=organisation, at=at))


def signatories(organisation: str, at=None) -> list[str]:
	return [r["user"] for r in _rows("organisation_signatories", organisation, at)]


def representatives(organisation: str, at=None) -> list[str]:
	return [r["user"] for r in _rows("organisation_people", organisation, at) if r.get("responsibility") == "Supplier Representative"]
