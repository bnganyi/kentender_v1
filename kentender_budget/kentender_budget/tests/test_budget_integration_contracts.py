# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 §12 logical integration contracts — resolve_budget_context,
revalidate_reservation, convert_reservation, adjust_commitment,
ingest_expenditure_snapshot.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.budget_authorization_seed import upsert_budget_test_authorization
from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_commitment_contracts import (
	adjust_commitment,
	convert_reservation,
	ingest_expenditure_snapshot,
)
from kentender_budget.services.budget_contracts import resolve_budget_context
from kentender_budget.services.budget_check_reserve_contracts import (
	release_reservation,
	reserve_funding,
	revalidate_reservation,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles


def _line(code: str) -> str:
	return frappe.db.get_value("Budget Line", {"generated_reference": code}, "name")


class TestResolveBudgetContext(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def test_resolves_active_baseline_for_pe_and_fy(self):
		ctx = resolve_budget_context(procuring_entity="PE-MOH", fiscal_period="2027/28")
		self.assertEqual(ctx["code"], "MOH-BUD-2027-2028")
		self.assertEqual(ctx["status"], "Active")
		self.assertEqual(ctx["procuring_entity"]["code"], "PE-MOH")

	def test_zero_baseline_is_a_typed_not_found_error(self):
		with self.assertRaises(frappe.DoesNotExistError):
			resolve_budget_context(procuring_entity="PE-MOH", fiscal_period="1999/00")

	def test_missing_fiscal_period_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			resolve_budget_context(procuring_entity="PE-MOH", fiscal_period="")


class TestBudgetCommitmentContracts(FrappeTestCase):
	"""Exercises BUD-CHG-001 §13.1's canonical arithmetic fixture end to end:
	480M approved -> 455M reservation -> 310M commitment -> 145M remaining
	reservation -> 25M available.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		upsert_budget_test_authorization()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def _drop_test_artifacts(self) -> None:
		# The Budget test suite does not roll back service-created (non-fixture
		# -namespaced) records between test runs — mirrors test_budget_check_reserve.py's
		# own explicit cleanup convention. Reservations are the root of the chain
		# (commitment.reservation / snapshot.commitment), so delete children first.
		rsv_names = frappe.get_all(
			"Funding Reservation", filters={"plan_item_code": ["like", "PPI-TEST-%"]}, pluck="name"
		)
		for doctype, filters in (
			("Expenditure Snapshot", {"source_system": ["like", "Test %"]}),
			("Procurement Commitment", {"reservation": ["in", rsv_names or [""]]}),
			("Funding Reservation", {"plan_item_code": ["like", "PPI-TEST-%"]}),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def setUp(self):
		self._drop_test_artifacts()
		upsert_moh_mvp_v1_portfolio()
		self.line_name = _line("MOH-BL-DHI-2027")
		# Isolate: this fixture's own reservation/commitment prior state is 0/0.
		frappe.db.set_value(
			"Budget Line", self.line_name, {"amount_reserved": 0, "amount_committed": 0}
		)

	def tearDown(self):
		self._drop_test_artifacts()

	def _reserve(self, key_suffix: str, amount: float = 455_000_000) -> dict:
		return reserve_funding(
			budget_line=self.line_name,
			plan_item_code=f"PPI-TEST-{key_suffix}",
			requested_amount=amount,
			idempotency_key=f"TEST:{key_suffix}:RSV",
		)

	def test_convert_reservation_matches_canonical_fixture(self):
		rsv = self._reserve("CONV-131")
		conv = convert_reservation(
			reservation=rsv["reservation_id"],
			contract_code="CTR-TEST-131",
			contract_title="Test 13.1 fixture contract",
			commitment_amount=310_000_000,
			idempotency_key="TEST:CONV-131:COMMIT",
		)
		self.assertTrue(conv["ok"])
		self.assertFalse(conv["reused"])
		self.assertEqual(flt(conv["current_amount"]), 310_000_000)

		rsv_doc = frappe.get_doc("Funding Reservation", rsv["reservation_id"])
		self.assertEqual(rsv_doc.status, "Partially converted")
		self.assertEqual(flt(rsv_doc.remaining_reserved), 145_000_000)

		line = frappe.get_doc("Budget Line", self.line_name)
		self.assertEqual(flt(line.amount_reserved), 145_000_000)
		self.assertEqual(flt(line.amount_committed), 310_000_000)
		available = flt(line.approved_amount) - flt(line.amount_reserved) - flt(line.amount_committed)
		self.assertEqual(available, 25_000_000)

	def test_convert_reservation_rejects_excess(self):
		rsv = self._reserve("CONV-EXCESS")
		with self.assertRaises(frappe.ValidationError):
			convert_reservation(
				reservation=rsv["reservation_id"],
				contract_code="CTR-TEST-EXCESS",
				commitment_amount=999_000_000,
			)

	def test_convert_reservation_idempotent_same_key(self):
		rsv = self._reserve("CONV-IDEM")
		key = "TEST:CONV-IDEM:COMMIT"
		first = convert_reservation(
			reservation=rsv["reservation_id"], contract_code="CTR-IDEM", commitment_amount=100_000_000,
			idempotency_key=key,
		)
		second = convert_reservation(
			reservation=rsv["reservation_id"], contract_code="CTR-IDEM", commitment_amount=100_000_000,
			idempotency_key=key,
		)
		self.assertTrue(second["reused"])
		self.assertEqual(first["commitment_code"], second["commitment_code"])
		line = frappe.get_doc("Budget Line", self.line_name)
		# A reused (not re-applied) conversion must not double-count the commitment.
		self.assertEqual(flt(line.amount_committed), 100_000_000)

	def test_full_conversion_marks_reservation_converted(self):
		rsv = self._reserve("CONV-FULL", amount=50_000_000)
		convert_reservation(
			reservation=rsv["reservation_id"],
			contract_code="CTR-FULL",
			commitment_amount=50_000_000,
			idempotency_key="TEST:CONV-FULL:COMMIT",
		)
		rsv_doc = frappe.get_doc("Funding Reservation", rsv["reservation_id"])
		self.assertEqual(rsv_doc.status, "Converted")
		self.assertEqual(flt(rsv_doc.remaining_reserved), 0)

	def test_adjust_commitment_updates_line_and_outstanding(self):
		rsv = self._reserve("ADJ-001")
		conv = convert_reservation(
			reservation=rsv["reservation_id"], contract_code="CTR-ADJ", commitment_amount=200_000_000,
			idempotency_key="TEST:ADJ-001:COMMIT",
		)
		adjusted = adjust_commitment(
			commitment=conv["commitment_id"], new_amount=220_000_000, reason="Variation +20M"
		)
		self.assertEqual(flt(adjusted["current_amount"]), 220_000_000)
		line = frappe.get_doc("Budget Line", self.line_name)
		self.assertEqual(flt(line.amount_committed), 220_000_000)

	def test_adjust_commitment_blocks_increase_beyond_available(self):
		rsv = self._reserve("ADJ-BLOCK", amount=100_000_000)
		conv = convert_reservation(
			reservation=rsv["reservation_id"], contract_code="CTR-ADJ-BLOCK", commitment_amount=100_000_000,
			idempotency_key="TEST:ADJ-BLOCK:COMMIT",
		)
		with self.assertRaises(frappe.ValidationError):
			adjust_commitment(
				commitment=conv["commitment_id"], new_amount=999_000_000, reason="Too large"
			)

	def test_adjust_commitment_requires_reason(self):
		rsv = self._reserve("ADJ-REASON")
		conv = convert_reservation(
			reservation=rsv["reservation_id"], contract_code="CTR-ADJ-REASON", commitment_amount=50_000_000,
			idempotency_key="TEST:ADJ-REASON:COMMIT",
		)
		with self.assertRaises(frappe.ValidationError):
			adjust_commitment(commitment=conv["commitment_id"], new_amount=60_000_000, reason="")

	def test_ingest_expenditure_snapshot_updates_line_and_commitment(self):
		rsv = self._reserve("EXP-001")
		conv = convert_reservation(
			reservation=rsv["reservation_id"], contract_code="CTR-EXP", commitment_amount=200_000_000,
			idempotency_key="TEST:EXP-001:COMMIT",
		)
		snap = ingest_expenditure_snapshot(
			budget_line=self.line_name,
			commitment=conv["commitment_id"],
			amount=120_000_000,
			source_system="Test Finance System",
			source_reference="FIN-TEST-EXP-001",
			source_as_at=str(frappe.utils.today()),
			idempotency_key="TEST:EXP-001:SNAP",
		)
		self.assertTrue(snap["ok"])
		self.assertEqual(snap["reconciliation_status"], "Matched")
		line = frappe.get_doc("Budget Line", self.line_name)
		self.assertEqual(flt(line.amount_actual), 120_000_000)
		com = frappe.get_doc("Procurement Commitment", conv["commitment_id"])
		self.assertEqual(flt(com.actual_expenditure), 120_000_000)
		self.assertEqual(flt(com.outstanding_amount), 80_000_000)

	def test_ingest_expenditure_snapshot_idempotent_same_key(self):
		key = "TEST:EXP-IDEM:SNAP"
		first = ingest_expenditure_snapshot(
			budget_line=self.line_name, amount=10_000_000, source_system="Test Finance System",
			idempotency_key=key,
		)
		second = ingest_expenditure_snapshot(
			budget_line=self.line_name, amount=999_000_000, source_system="Test Finance System",
			idempotency_key=key,
		)
		self.assertTrue(second["reused"])
		self.assertEqual(first["snapshot_id"], second["snapshot_id"])
		self.assertEqual(flt(second["amount"]), 10_000_000)

	def test_revalidate_reservation_stays_valid_without_estimate_change(self):
		rsv = self._reserve("REVAL-OK")
		result = revalidate_reservation(
			reservation=rsv["reservation_id"], material_event="Budget Revision applied", evidence="REV-TEST-OK"
		)
		self.assertTrue(result["valid"])
		self.assertEqual(result["status"], "Reserved")

	def test_revalidate_reservation_needs_attention_on_increase_beyond_available(self):
		rsv = self._reserve("REVAL-ATTN", amount=100_000_000)
		result = revalidate_reservation(
			reservation=rsv["reservation_id"],
			material_event="Tender estimate increased",
			new_estimated_amount=500_000_000,
			evidence="TND-TEST-ATTN",
		)
		self.assertFalse(result["valid"])
		self.assertEqual(result["status"], "Needs attention")
		rsv_doc = frappe.get_doc("Funding Reservation", rsv["reservation_id"])
		self.assertEqual(rsv_doc.status, "Needs attention")
		self.assertTrue(
			frappe.db.exists(
				"Budget Audit Event",
				{"record_code": rsv["reservation_code"], "event_type": "Reservation revalidated"},
			)
		)

	def test_revalidate_reservation_requires_material_event(self):
		rsv = self._reserve("REVAL-NOEVT")
		with self.assertRaises(frappe.ValidationError):
			revalidate_reservation(reservation=rsv["reservation_id"], material_event="")

	def test_revalidate_reservation_rejects_terminal_status(self):
		rsv = self._reserve("REVAL-TERM")
		release_reservation(reservation=rsv["reservation_id"], reason="Cancelled for test")
		with self.assertRaises(frappe.ValidationError):
			revalidate_reservation(reservation=rsv["reservation_id"], material_event="Any event")
