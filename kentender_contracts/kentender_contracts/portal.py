# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract Management's supplier portal surface (`kt_portal_surfaces`; CM-CHG-001 v0.8 section 9: "Supplier list `/supplier/contracts`; detail `/supplier/contracts/{id}`"). Answers `/supplier/contracts` and
`/supplier/contracts/<contract>[/<tab>[/<subject...>]]` for a signed-in supplier person; the screens load through the same two reads the Desk page uses (`api.workspace`, `api.contract`), so a supplier sees
exactly the supplier projection and nothing the Desk shows an internal reader. A signed-out visitor is sent to sign in; a contract the person may not read is masked exactly like one that does not exist."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.services import audience

NOT_FOUND = {"verdict": "NOT_FOUND", "title": "Page not found", "payload": {"screen": "not-found"}}
PREFIX = ["supplier", "contracts"]


def resolve(*, path: str, query: dict[str, Any], user: str) -> dict[str, Any]:
	segments = [s for s in path.split("/") if s]
	if not user or user == "Guest":
		return {"verdict": "SIGN_IN", "title": "Sign in"}
	if segments[:2] != PREFIX:
		return NOT_FOUND
	rest = segments[2:]
	if not rest:
		return {"verdict": "OK", "title": "My contracts", "payload": {"screen": "contracts"}}
	contract = rest[0]
	if not frappe.db.exists("Contract Case", contract) or not audience.readable(user, contract):
		return NOT_FOUND
	return {"verdict": "OK", "title": contract, "payload": {"screen": "contracts", "contract": contract}}
