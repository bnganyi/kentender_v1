# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A test candidate registry for the Tenders tests (TPR FU-25).

Bid Submission's Start bid is the only way a real candidate registers; the
Tenders tests must not depend on it, so they register candidates in this
in-memory provider, installed through the `frappe.flags` override
`candidate_gateway` honours. It answers the same two contract functions as
the Bid Submission provider: `candidate_audience(*, tender, at)` and
`candidate_registration(*, tender, candidate_registration_id)`."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.tenders.services import clock


class FakeCandidates:
	def __init__(self) -> None:
		self.rows: list[dict[str, Any]] = []

	def register(self, *, tender: str, bidder_arrangement_id: str, candidate_name: str, notice_address: str, registered_at=None) -> str:
		self.rows.append({
			"tender": tender, "candidate_registration_id": bidder_arrangement_id, "candidate_name": candidate_name, "destination": notice_address,
			"destination_version": "1", "registered_at": get_datetime(registered_at) if registered_at else clock.now(),
		})
		return bidder_arrangement_id

	def candidate_audience(self, *, tender: str, at=None) -> list[dict[str, Any]]:
		instant = get_datetime(at or clock.now())
		return [
			{"candidate_registration_id": r["candidate_registration_id"], "destination": r["destination"], "destination_version": r["destination_version"]}
			for r in self.rows if r["tender"] == tender and r["registered_at"] <= instant
		]

	def candidate_registration(self, *, tender: str, candidate_registration_id: str) -> dict[str, Any] | None:
		for r in self.rows:
			if r["tender"] == tender and r["candidate_registration_id"] == cstr(candidate_registration_id).strip():
				return {k: r[k] for k in ("candidate_registration_id", "candidate_name", "destination", "destination_version", "registered_at")}
		return None


def install(testcase) -> FakeCandidates:
	"""Install a fresh registry for one test and restore the previous one after."""
	fake = FakeCandidates()
	previous = frappe.flags.get("kt_tender_candidate_registry")
	frappe.flags.kt_tender_candidate_registry = fake
	testcase.addCleanup(frappe.flags.__setitem__, "kt_tender_candidate_registry", previous)
	return fake
