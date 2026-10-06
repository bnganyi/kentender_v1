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

	def can_read_row(self, owner_id: str, user: str) -> bool:
		"""May this reader see this opening as a row of the Procurement meetings
		register (OVS-CHG-001 v0.6 §11)? The opening's own readers, and a Head of
		User Department whose unit contributed to the Tender. A row carries facts
		about the meeting only; the opening record applies its own rule again."""
		from kentender_procurement.bid_opening.services import reads
		from kentender_procurement.tenders.services import tender_authorization as authz

		if reads.can_read(owner_id, user):
			return True
		tender = frappe.db.get_value(CASE, owner_id, "tender")
		return bool(tender) and authz.is_department_head_of(frappe.get_doc("Tender", tender), user)


def adapters() -> dict[str, Any]:
	return {OWNER_TYPE: BidOpeningOwner()}
