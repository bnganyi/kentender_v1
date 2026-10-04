# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening as the owner of its Proceeding (PRC-CHG-001 v0.9 §3, §7.1;
BOP-CHG-001 v0.10 §7.1; plan D1).

Registered on the `kt_prc_owner_adapters` hook for owner type "Bid Opening
Case". Proceedings is reachable only from inside a Bid Opening command or
read, after Bid Opening has applied its own statutory guards, appointment,
presence and disclosure rules: the adapter allows an act only while
`acting(case)` is in force for that case. A direct call from anywhere else
is refused. Proceedings still applies its own checks (a technical user is
refused; a member attests only their own target on the current version)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe

OWNER_TYPE = "Bid Opening Case"
CASE = "Bid Opening Case"


@contextmanager
def acting(case: str | None):
	previous = getattr(frappe.local, "kt_bop_owner_context", None)
	frappe.local.kt_bop_owner_context = (previous or frozenset()) | ({case} if case else set())
	try:
		yield
	finally:
		frappe.local.kt_bop_owner_context = previous


class BidOpeningOwner:
	def exists(self, owner_id: str) -> bool:
		return bool(frappe.db.exists(CASE, owner_id))

	def allows(self, owner_id: str, user: str, capacity: str) -> bool:
		return owner_id in (getattr(frappe.local, "kt_bop_owner_context", None) or frozenset())


def adapters() -> dict[str, Any]:
	return {OWNER_TYPE: BidOpeningOwner()}
