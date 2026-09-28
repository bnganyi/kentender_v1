# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published seam between Supplier Accounts (kentender_suppliers) and Bid
Submission (kentender_procurement) — BDS-CHG-001 v0.8 plan D1. Procurement
installs before Suppliers and never imports it; it asks this module for the
provider registered on the `kt_supplier_account_provider` hook. Without one
a caller must fail closed (no Account, no bid).

A provider module exposes exactly `FUNCTIONS`; every function takes keyword
arguments and returns plain dicts/lists (identity and access facts only —
never evidence bytes except through `evidence_file`). Tests may set
`frappe.flags.kt_supplier_account_provider` to a provider object."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_supplier_account_provider"
FUNCTIONS: tuple[str, ...] = (
	"active_assignments",  # (*, user, at=None) -> [assignment]
	"assignment",  # (*, assignment_id) -> assignment | None
	"organisation",  # (*, organisation_id) -> facts | None
	"verified_contacts",  # (*, organisation_id) -> [verified email contact]
	"account_evidence",  # (*, organisation_id) -> [evidence metadata]
	"evidence_file",  # (*, organisation_id, evidence_id) -> {file_name, content, digest} | None
	"find_active_account",  # (*, country, registration_number) -> {organisation_id, legal_name} | None
	"organisation_signatories",  # (*, organisation_id, at=None) -> [assignment of an Authorised Signatory who can sign now]
	"organisation_people",  # (*, organisation_id, at=None) -> [active assignment of a Supplier Representative or Authorised Signatory]
)


def provider() -> Any | None:
	override = frappe.flags.get("kt_supplier_account_provider")
	if override:
		return frappe.get_module(override) if isinstance(override, str) else override
	paths = frappe.get_hooks(HOOK) or []
	return frappe.get_module(paths[-1]) if paths else None


def missing_functions(candidate: Any) -> list[str]:
	"""The contract functions a provider lacks (the contract test)."""
	return [name for name in FUNCTIONS if not callable(getattr(candidate, name, None))]
