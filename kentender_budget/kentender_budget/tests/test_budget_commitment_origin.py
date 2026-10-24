# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.16 section 4.6 and BUD24-XD-001 (BUD25-AC-001, -011): a commitment carries the Budget Line it is charged to, whichever way it was made.

A commitment made by converting a reservation reaches its line through the reservation; one made by an approved existing-contract entry has no reservation. Every reader of Committed must therefore read the
line from the commitment, so that the two count alike. These tests prove the parity, the rules of the record, the migration of the rows that already exist, and that no reader joins commitments to reservations
for a line total any more."""

from __future__ import annotations

from pathlib import Path

import frappe

from kentender_budget.patches.bud_chg_001_v1_16_commitment_carries_its_line import execute as migrate
from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services import budget_downstream_contracts as lineage_read
from kentender_budget.services.budget_contracts import _line_position_exact
from kentender_budget.services.budget_reference import allocate_commitment_reference
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller
from kentender_budget.services.budget_write_family import budget_write
from kentender_budget.tests.test_bud_chg_001_v19_usability import _V19Base
from kentender_core.services.command_write_guard import purge_doc

DHI = "Digital health infrastructure programme"


class TestACommitmentCarriesItsLine(_V19Base):
	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for budget in cls._budgets:
			for name in frappe.get_all("Procurement Commitment", filters={"budget": budget}, pluck="name"):
				purge_doc("Procurement Commitment", name)
		super().tearDownClass()

	def setUp(self):
		super().setUp()
		self.contract = f"CTR-ORIGIN-{self.suffix}-{frappe.generate_hash(length=4)}"
		self.fy, self.budget, self.v1 = self._active()
		self.dhi = self._line(self.v1, DHI)

	def position(self):
		return {k: float(v) for k, v in _line_position_exact(self.dhi, commit._current_line_version(self.dhi)).items()}

	def entry_commitment(self, amount, *, status="Active", **overrides):
		values = {"doctype": "Procurement Commitment", "generated_reference": allocate_commitment_reference(), "origin": "Existing-contract entry", "budget": self.budget, "budget_line": self.dhi,
			"entry_row": f"ENTRY/{frappe.generate_hash(length=6)}", "contract": self.contract, "status": status, "current_amount": amount, "currency": "KES", **overrides}
		doc = frappe.get_doc(values)
		with budget_write():
			doc.insert(ignore_permissions=True)
		return doc

	def conversion(self, amount):
		reservation = self._reserve(self.dhi, amount, ref=f"REQ-{self.contract}")
		self._as("Administrator")
		done = commit.convert_reservation(reservation, self.contract, amount, f"conv-{frappe.generate_hash(length=8)}", contract_event_id="e1", contract_event_type="ContractEffective",
			caller=service_caller(PRINCIPAL_CONTRACT, reference=self.contract))
		return reservation, done["commitment"]["commitment_id"]

	# parity ----------------------------------------------------------------------------------------------------------------------
	def test_a_commitment_with_no_reservation_counts_in_the_line_position_exactly_like_one_with_a_reservation(self):
		before = self.position()
		self.entry_commitment(1_000_000)
		after_entry = self.position()
		self.assertEqual((after_entry["committed"], after_entry["available"], after_entry["reserved"]), (before["committed"] + 1_000_000, before["available"] - 1_000_000, before["reserved"]))
		reservation, commitment = self.conversion(2_000_000)
		after_conversion = self.position()
		self.assertEqual(after_conversion["committed"], after_entry["committed"] + 2_000_000, "both origins add to the same Committed figure")
		self.assertEqual((after_conversion["available"], after_conversion["reserved"]), (after_entry["available"] - 2_000_000, after_entry["reserved"]), "the reservation took 2m from Available and the conversion moved it from reserved to committed")

	def test_closed_commitments_of_either_origin_stay_counted_and_cancelled_ones_do_not(self):
		before = self.position()
		self.entry_commitment(500_000, status="Closed")
		self.entry_commitment(700_000, status="Cancelled")
		self.assertEqual(self.position()["committed"], before["committed"] + 500_000)

	def test_the_funding_lineage_read_finds_an_entry_commitment_by_its_contract(self):
		made = self.entry_commitment(250_000)
		self._as("Administrator")
		rows = lineage_read.get_funding_lineage(contract=self.contract)["rows"]
		found = [c for row in rows for c in row["commitments"] if c["id"] == made.name]
		self.assertEqual(len(found), 1)
		self.assertTrue(any(row.get("reservation") is None and row.get("origin") == "Existing-contract entry" for row in rows))

	# the rules of the record ------------------------------------------------------------------------------------------------------
	def test_a_conversion_commitment_takes_its_line_and_budget_from_its_reservation(self):
		reservation, commitment = self.conversion(1_000_000)
		row = frappe.db.get_value("Procurement Commitment", commitment, ["origin", "budget_line", "budget", "reservation", "entry_row"], as_dict=True)
		self.assertEqual((row.origin, row.budget_line, row.budget, row.reservation, row.entry_row), ("Reservation conversion", self.dhi, self.budget, reservation, None))

	def test_a_conversion_cannot_be_charged_to_another_line_than_its_reservations(self):
		reservation = self._reserve(self.dhi, 1_000_000, ref=f"REQ-X-{self.contract}")
		other = self._line(self.v1, "Digital health workforce development")
		doc = frappe.get_doc({"doctype": "Procurement Commitment", "generated_reference": allocate_commitment_reference(), "reservation": reservation, "budget_line": other, "contract": self.contract,
			"status": "Active", "current_amount": 1, "currency": "KES"})
		with budget_write(), self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_a_conversion_must_name_its_reservation_and_an_entry_commitment_must_not(self):
		for label, values in (("conversion without a reservation", {"origin": "Reservation conversion", "reservation": None, "entry_row": ""}),
			("entry with a reservation", {"origin": "Existing-contract entry", "reservation": self._reserve(self.dhi, 10, ref=f"REQ-R-{self.contract}")}),
			("entry without a row", {"origin": "Existing-contract entry", "entry_row": ""}), ("entry without a line", {"origin": "Existing-contract entry", "budget_line": None})):
			with self.subTest(label), budget_write(), self.assertRaises((frappe.ValidationError, frappe.MandatoryError)):
				frappe.get_doc({"doctype": "Procurement Commitment", "generated_reference": allocate_commitment_reference(), "budget": self.budget, "budget_line": self.dhi, "entry_row": "E/1", "contract": self.contract,
					"status": "Active", "current_amount": 1, "currency": "KES", **values}).insert(ignore_permissions=True)

	def test_an_entry_row_is_unique_per_contract_and_the_same_row_cannot_fund_twice(self):
		first = self.entry_commitment(1_000)
		with budget_write(), self.assertRaises((frappe.DuplicateEntryError, frappe.UniqueValidationError)):
			self.entry_commitment(1_000, entry_row=first.entry_row)

	# the migration of what already exists -------------------------------------------------------------------------------------------
	def test_the_migration_gives_existing_commitments_their_reservations_line_and_budget_and_is_repeatable(self):
		reservation, commitment = self.conversion(1_000_000)
		frappe.db.sql("update `tabProcurement Commitment` set budget_line = null, budget = null, origin = '' where name = %s", commitment)
		migrate()
		migrate()
		row = frappe.db.get_value("Procurement Commitment", commitment, ["origin", "budget_line", "budget", "entry_row"], as_dict=True)
		self.assertEqual((row.origin, row.budget_line, row.budget, row.entry_row), ("Reservation conversion", self.dhi, self.budget, None))
		self.assertTrue(frappe.db.has_index("tabProcurement Commitment", "uq_commitment_entry_row"))
		self.assertTrue(frappe.db.has_index("tabProcurement Commitment", "uq_commitment_contract_reservation"), "the v1.12 key for conversions stays")

	# no reader joins commitments to reservations for a line total ------------------------------------------------------------------------
	def test_no_reader_derives_a_lines_committed_total_through_its_reservations(self):
		root = Path(frappe.get_app_path("kentender_budget")).parents[1]
		anti_patterns = ("where reservation in %s and status in ('Active', 'Closed')", "join `tabFunding Reservation` r on r.name = c.reservation where r.budget_line", "reservation in %s and status in ('Active', 'Closed')")
		offenders = []
		for path in sorted(p for app in root.glob("kentender_*") for p in app.rglob("*.py")):
			relative = str(path.relative_to(root))
			if "/tests/" in relative or relative.endswith("test_budget_commitment_origin.py"):
				continue
			text = path.read_text()
			offenders += [f"{relative}: {pattern}" for pattern in anti_patterns if pattern in text]
		self.assertEqual(offenders, [])
