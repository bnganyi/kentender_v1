# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The one door from Bid Submission into Supplier Accounts (BDS-CHG-001 v0.8
plan D1). Procurement installs before Suppliers and never imports it: the
provider comes from the `kt_supplier_account_provider` hook through
kentender_core. Without a provider nothing can start or change a bid, so
every read fails closed as "no supplier account"."""

from __future__ import annotations

from typing import Any

from kentender_core.services import supplier_account_contract as contract

from kentender_procurement.bid_submission.services.errors import fail


def _provider():
	provider = contract.provider()
	if provider is None:
		fail("BDS_ACCOUNT_REQUIRED")
	return provider


def active_assignments(*, user: str, at=None) -> list[dict[str, Any]]:
	return list(_provider().active_assignments(user=user, at=at))


def assignment(*, assignment_id: str, at=None) -> dict[str, Any] | None:
	return _provider().assignment(assignment_id=assignment_id, at=at) if assignment_id else None


def organisation(*, organisation_id: str) -> dict[str, Any] | None:
	return _provider().organisation(organisation_id=organisation_id) if organisation_id else None


def verified_contacts(*, organisation_id: str) -> list[dict[str, Any]]:
	return list(_provider().verified_contacts(organisation_id=organisation_id))


def account_evidence(*, organisation_id: str) -> list[dict[str, Any]]:
	return list(_provider().account_evidence(organisation_id=organisation_id))


def find_active_account(*, country: str, registration_number: str) -> dict[str, Any] | None:
	return _provider().find_active_account(country=country, registration_number=registration_number)


def evidence_file(*, organisation_id: str, evidence_id: str) -> dict[str, Any] | None:
	"""The exact bytes and digest of an Account evidence file (reused in a bid)."""
	return _provider().evidence_file(organisation_id=organisation_id, evidence_id=evidence_id)
