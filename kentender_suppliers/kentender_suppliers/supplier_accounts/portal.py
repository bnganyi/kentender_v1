# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier Accounts' portal surface (`kt_portal_surfaces`; BDS-CHG-001 v0.8
plan OD-B, slices 11.3–11.4). Answers `/account` (BDS-DES-04, or BDS-DES-03
when the person has no Account yet), `/account/register` (BDS-DES-03) and
`/account/verify` (the verification link). Every path needs a signed-in
person; a signed-out visitor is sent to sign in and back. The first payload
is the same `GetSupplierAccount` read the screen reloads (KT-STD-001 §3A.1).
`/account/receipts` belongs to Bid Submission (a longer prefix)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_suppliers.supplier_accounts.services import guidance, read

NOT_FOUND = {"verdict": "NOT_FOUND", "title": "Page not found", "payload": {"screen": "not-found"}}
TITLES = {"register": "Set up your supplier account", "account": "Account", "verify": "Verify your contact", "choose": "Account"}


def resolve(*, path: str, query: dict[str, Any], user: str) -> dict[str, Any]:
	segments = [s for s in path.split("/") if s]
	if not user or user == "Guest":
		return {"verdict": "SIGN_IN", "title": "Sign in"}
	if segments == ["account", "verify"]:
		return {"verdict": "OK", "title": TITLES["verify"], "payload": {"screen": "verify", "data": {"token": cstr(query.get("token"))}}}
	if segments == ["account", "register"]:
		return {"verdict": "OK", "title": TITLES["register"], "payload": {"screen": "register", "data": {"user": user, "user_name": guidance.full_name(user), **guidance.for_new_account(user)}}}
	if segments == ["account"]:
		try:
			data = read.get_supplier_account(organisation=cstr(query.get("organisation")), user=user)
		except frappe.DoesNotExistError:
			return NOT_FOUND  # another organisation's Account is masked exactly like a missing one
		if data["state"] == "no_account":
			return {"verdict": "OK", "title": TITLES["register"], "payload": {"screen": "register", "data": {"user": user, "user_name": guidance.full_name(user), **data}}}
		screen = "account" if data["state"] == "account" else "choose"
		return {"verdict": "OK", "title": TITLES[screen], "payload": {"screen": screen, "data": {"outcome": "OK", **data}}}
	return NOT_FOUND


def identity_detail(user: str) -> str:
	"""The line under a signed-in supplier's name in the portal header: the
	organisation they act for (or how many, when they act for several). Staff
	and people without an Account get nothing."""
	from kentender_suppliers.supplier_accounts.services import authorization as authz

	if not user or user == "Guest" or authz.is_internal_user(user):
		return ""
	organisations = authz.organisations_of(user)
	if len(organisations) > 1:
		return f"{len(organisations)} organisations"
	return cstr(frappe.db.get_value("Supplier Organisation", organisations[0], "legal_name")) if organisations else ""
