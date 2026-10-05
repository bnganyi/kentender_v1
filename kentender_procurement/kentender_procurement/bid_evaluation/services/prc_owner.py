# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Evaluation as the owner of its Proceeding (EVL-CHG-001 v0.4 §6, plan D4).

Registered on the `kt_prc_owner_adapters` hook for owner type "Evaluation
Case", with the Bid Evaluation profile. Proceedings is reachable only from
inside a Bid Evaluation command or read, after Evaluation has applied its own
appointment, eligibility, presence and disclosure rules: the adapter allows
an act only while `acting(case)` is in force for that case. Proceedings still
applies its own checks (a technical user is refused; a member proves only
their own current target; a conclusion needs the required roster present)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe

OWNER_TYPE = "Evaluation Case"
CASE = "Evaluation Case"


@contextmanager
def acting(case: str | None):
	previous = getattr(frappe.local, "kt_evl_owner_context", None)
	frappe.local.kt_evl_owner_context = (previous or frozenset()) | ({case} if case else set())
	try:
		yield
	finally:
		frappe.local.kt_evl_owner_context = previous


class EvaluationOwner:
	proceeding_type = "Bid Evaluation"

	def exists(self, owner_id: str) -> bool:
		return bool(frappe.db.exists(CASE, owner_id))

	def allows(self, owner_id: str, user: str, capacity: str) -> bool:
		return owner_id in (getattr(frappe.local, "kt_evl_owner_context", None) or frozenset())

	def can_read_row(self, owner_id: str, user: str) -> bool:
		"""May this reader see this evaluation's sessions as rows of the Procurement
		meetings register (OVS-CHG-001 v0.6 §11)? Anyone who may read the evaluation
		at all (an office, a member, the secretary, an auditor, a technical reader, a
		department head whose unit contributed). A row never carries a session's
		subject or notes; the evaluation applies its own disclosure again."""
		from kentender_procurement.bid_evaluation.services import reads

		return bool(reads.access(frappe.get_doc(CASE, owner_id), user)["read"])


def adapters() -> dict[str, Any]:
	return {OWNER_TYPE: EvaluationOwner()}
