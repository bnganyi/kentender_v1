# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One contract, read once for one viewer (CM-CHG-001 v0.8 sections 6.2, 6.3).

Every board builder needs the same facts: the case, its current agreement and terms, the delivery position, the appointment, the arrivals and the current inspection, the acceptance reports, the
invoices and payments, and the viewer's own next step. They are gathered here, lazily and once, so a builder reads like the board it draws and no builder reaches into another module's tables. The
viewer's audiences (`audience.py`) decide what a builder may draw; `ctx.sees("money_native")` asks that question for a field set."""

from __future__ import annotations

from functools import cached_property
from typing import Any

import frappe
from frappe.utils import cint, flt

from kentender_contracts.services import audience, bindings, clock, delivery, formation, payment, people, position, records, work


def money(value: Any, currency: str = "KES") -> str:
	return f"{currency} {flt(value):,.0f}"


def when(value) -> str:
	return clock.when(value) if value else ""


class Context:
	def __init__(self, case: str, user: str):
		self.case, self.user = case, user
		self.grants = audience.readable(user, case)

	def sees(self, field_set: str) -> bool:
		return field_set in audience.field_sets(self.grants)

	@property
	def audiences(self) -> list[str]:
		return [g.audience for g in self.grants]

	@cached_property
	def doc(self):
		return frappe.get_doc("Contract Case", self.case)

	@cached_property
	def agreement(self):
		return formation.current_agreement(self.case)

	@cached_property
	def assembled(self) -> dict[str, Any]:
		"""Before an agreement is saved the preparer still sees what would be generated, read from the sources without writing anything. A source that cannot be verified is reported, not hidden."""
		if self.agreement:
			return {"terms": records.loads(self.agreement.terms_json), "missing": records.loads(self.agreement.missing_json, []), "failed": []}
		from kentender_contracts.services.errors import ContractError

		try:
			built = formation._assemble(self.doc, {})
			return {"terms": built["terms"], "missing": built["missing"], "failed": []}
		except ContractError as exc:
			return {"terms": {}, "missing": [], "failed": exc.detail.get("failed", [])}

	@cached_property
	def terms(self) -> dict[str, Any]:
		return self.assembled["terms"]

	@cached_property
	def currency(self) -> str:
		return self.terms.get("currency") or self.doc.currency or "KES"

	@cached_property
	def position(self) -> dict[str, Any]:
		return position.position(self.case) if self.doc.lifecycle in ("Active", "Closed") else {"lines": {}, "units": {}, "ordered": 0, "accepted": 0, "arrived": 0, "in_custody": 0, "remaining": 0}

	@cached_property
	def appointment(self) -> dict[str, Any]:
		return delivery.appointment_state(self.case)

	@cached_property
	def proposal(self):
		name = frappe.db.get_value("Contract Appointment", {"contract_case": self.case, "state": "Recommended"}, "name", order_by="version_no desc")
		return frappe.get_doc("Contract Appointment", name) if name else None

	@cached_property
	def arrivals(self) -> list[dict[str, Any]]:
		return position.arrivals(self.case)

	@cached_property
	def signatures(self) -> list[dict[str, Any]]:
		if not self.agreement:
			return []
		return frappe.get_all("Contract Signature", filters={"contract_case": self.case, "agreement_version": self.agreement.version_no},
			fields=["name", "party", "sequence", "signer", "capacity", "state", "proof_reference", "signed_at"], order_by="sequence asc")

	@cached_property
	def invoices(self) -> list[Any]:
		return [frappe.get_doc("Contract Invoice", n) for n in frappe.get_all("Contract Invoice", filters={"contract_case": self.case}, pluck="name", order_by="invoice_no asc")]

	@cached_property
	def visible_holders(self) -> set[str] | None:
		"""Whose work this viewer may see: everyone's for an internal reader, only the supplier's own side for a supplier (section 6.2: never internal Finance or procurement tasks)."""
		if "supplier" in self.audiences and len(self.audiences) == 1:
			from kentender_contracts.services import parties

			org = self.doc.supplier_organisation
			return {u.lower() for u in parties.signatories(org) + parties.representatives(org)} | {self.user.lower()}
		return None

	@cached_property
	def tasks(self) -> list[dict[str, Any]]:
		everything = work.live(self.case)
		return everything if self.visible_holders is None else [t for t in everything if t["holder"].lower() in self.visible_holders]

	@cached_property
	def view(self) -> dict[str, Any]:
		return work.view(self.case, self.user, neutral=self.neutral, holders=self.visible_holders)

	@cached_property
	def lead(self) -> dict[str, Any] | None:
		"""The leading obligation of the viewer's view (their own if they have one, otherwise whoever the case is waiting on), what the case's next step is drawn from."""
		return self.view["leading"] if not self.neutral else None

	@cached_property
	def neutral(self) -> bool:
		"""A reader with no personal work: technical, auditor and the read-only audiences (section 6.3 "Not involved")."""
		return set(self.audiences) <= {"technical", "auditor"} or not self.audiences

	def name(self, user: str) -> str:
		return people.full_name(user) if user else ""

	def mine(self, command: str, subject_prefix: str = "") -> dict[str, Any] | None:
		"""A live obligation of this viewer for a command (optionally for subjects with a prefix)."""
		for item in self.tasks:
			if item["holder"].lower() == self.user.lower() and item["command"] == command and item["subject"].startswith(subject_prefix) and item["state"] in ("actionable", "blocked"):
				return item
		return None

	def holder_of(self, command: str, subject_prefix: str = "") -> dict[str, Any] | None:
		"""Whoever holds a live obligation of this command (the first, by assignment)."""
		for item in self.tasks:
			if item["command"] == command and item["subject"].startswith(subject_prefix):
				return item
		return None
