# Copyright (c) 2026, KenTender and contributors
"""Budget Domain v2 — unit tests covering the updated balance formula and new fields.

Run:
  bench --site kentender.midas.com run-tests --app kentender_budget \
        --module kentender_budget.tests.test_budget_domain_v2
"""

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


def _make_budget(entity, plan, fiscal_year=2026):
	h = frappe.generate_hash(length=6)
	return frappe.get_doc({
		"doctype": "Budget",
		"budget_name": f"DomainV2 Test {h}",
		"procuring_entity": entity,
		"strategic_plan": plan,
		"fiscal_year": fiscal_year,
		"currency": "KES",
		"total_budget_amount": 10_000_000,
		"status": "Draft",
	}).insert(ignore_permissions=True)


def _make_line(budget, program, allocated=1_000_000):
	return frappe.get_doc({
		"doctype": "Budget Line",
		"budget_line_name": f"TestLine-{frappe.generate_hash(length=4)}",
		"budget": budget.name,
		"procuring_entity": budget.procuring_entity,
		"fiscal_year": budget.fiscal_year,
		"currency": "KES",
		"strategic_plan": budget.strategic_plan,
		"program": program,
		"amount_allocated": allocated,
	}).insert(ignore_permissions=True)


class TestBudgetDomainV2(IntegrationTestCase):
	# ── Fixtures ──────────────────────────────────────────────────────────────

	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"V2-{h}", f"V2 Test Entity {h}")

		self.plan = frappe.get_doc({
			"doctype": "Strategic Plan",
			"strategic_plan_name": f"DomainV2 Plan {h}",
			"procuring_entity": self.entity,
			"start_year": 2026, "end_year": 2030,
			"status": "Draft",
		}).insert(ignore_permissions=True)

		self.program = frappe.get_doc({
			"doctype": "Strategy Program",
			"strategic_plan": self.plan.name,
			"program_title": f"Prog-{h}", "order_index": 0,
		}).insert(ignore_permissions=True)

		self.budget = _make_budget(self.entity, self.plan.name)
		self.line = _make_line(self.budget, self.program.name, allocated=1_000_000)

	def tearDown(self):
		frappe.set_user("Administrator")
		# Budget Line on_trash requires force-delete flag
		frappe.flags.budget_line_force_delete = True
		try:
			for row in frappe.get_all("Budget Line", {"budget": self.budget.name}, pluck="name"):
				frappe.delete_doc("Budget Line", row, force=True, ignore_permissions=True)
			# Budget on_trash blocks non-Draft budgets — reset status before delete
			if frappe.db.get_value("Budget", self.budget.name, "status") not in ("Draft", None):
				frappe.db.set_value("Budget", self.budget.name, "status", "Draft")
			frappe.delete_doc("Budget", self.budget.name, force=True, ignore_permissions=True)
			for row in frappe.get_all("Strategy Program", {"strategic_plan": self.plan.name}, pluck="name"):
				frappe.delete_doc("Strategy Program", row, force=True, ignore_permissions=True)
			frappe.delete_doc("Strategic Plan", self.plan.name, force=True, ignore_permissions=True)
		finally:
			frappe.flags.budget_line_force_delete = False
		frappe.db.commit()

	# ── A1: Budget Line new fields ────────────────────────────────────────────

	def test_a1_budget_line_has_amount_committed_field(self):
		"""Budget Line DocType has amount_committed field."""
		self.line.reload()
		self.assertTrue(hasattr(self.line, "amount_committed"),
			"amount_committed field missing from Budget Line")

	def test_a1_budget_line_has_line_status_field(self):
		"""Budget Line has line_status defaulting to Active."""
		self.line.reload()
		self.assertEqual(self.line.line_status, "Active")

	def test_a1_budget_line_has_economic_classification_field(self):
		"""Budget Line has economic_classification field."""
		self.assertTrue(hasattr(self.line, "economic_classification"),
			"economic_classification field missing from Budget Line")

	def test_a1_budget_line_has_department_field(self):
		"""Budget Line has department field."""
		self.assertTrue(hasattr(self.line, "department"),
			"department field missing from Budget Line")

	def test_a1_budget_line_classification_can_be_saved(self):
		"""Economic classification and department can be set and saved."""
		frappe.flags.budget_control_service_write = True
		try:
			self.line.economic_classification = "Works"
			self.line.department = "Ministry of Infrastructure"
			self.line.save(ignore_permissions=True)
			self.line.reload()
			self.assertEqual(self.line.economic_classification, "Works")
			self.assertEqual(self.line.department, "Ministry of Infrastructure")
		finally:
			frappe.flags.budget_control_service_write = False

	# ── A5: Updated balance formula ───────────────────────────────────────────

	def test_a5_available_formula_excludes_commitment(self):
		"""available = allocated − reserved − committed − consumed."""
		frappe.flags.budget_control_service_write = True
		try:
			self.line.amount_reserved  = 200_000
			self.line.amount_committed = 300_000
			self.line.amount_consumed  = 100_000
			self.line.save(ignore_permissions=True)
		finally:
			frappe.flags.budget_control_service_write = False

		self.line.reload()
		expected = 1_000_000 - 200_000 - 300_000 - 100_000  # = 400_000
		self.assertAlmostEqual(flt(self.line.amount_available), expected, places=2)

	def test_a5_available_zero_when_fully_committed_and_reserved(self):
		"""available = 0 when reserved + committed = allocated."""
		frappe.flags.budget_control_service_write = True
		try:
			self.line.amount_reserved  = 600_000
			self.line.amount_committed = 400_000
			self.line.amount_consumed  = 0
			self.line.save(ignore_permissions=True)
		finally:
			frappe.flags.budget_control_service_write = False

		self.line.reload()
		self.assertAlmostEqual(flt(self.line.amount_available), 0, places=2)

	def test_a5_validation_rejects_reserved_plus_committed_plus_consumed_exceeds_allocated(self):
		"""BL-004 fires when reserved + committed + consumed > allocated."""
		frappe.flags.budget_control_service_write = True
		try:
			self.line.amount_reserved  = 500_000
			self.line.amount_committed = 400_000
			self.line.amount_consumed  = 200_000   # total = 1,100,000 > 1,000,000
			with self.assertRaises(ValidationError):
				self.line.save(ignore_permissions=True)
		finally:
			frappe.flags.budget_control_service_write = False

	def test_a5_committed_alone_cannot_exceed_allocated(self):
		"""Committed > allocated triggers BL-004."""
		frappe.flags.budget_control_service_write = True
		try:
			self.line.amount_reserved  = 0
			self.line.amount_committed = 1_100_000  # > 1,000,000
			self.line.amount_consumed  = 0
			with self.assertRaises(ValidationError):
				self.line.save(ignore_permissions=True)
		finally:
			frappe.flags.budget_control_service_write = False

	def test_a5_committed_field_is_service_controlled(self):
		"""Direct edit of amount_committed without flag raises an error."""
		self.line.reload()
		self.line.amount_committed = 50_000
		with self.assertRaises(ValidationError):
			self.line.save(ignore_permissions=True)

	def _budget_to_approved(self):
		"""Helper: advance budget Draft → Submitted → Approved (Administrator bypasses role check)."""
		self.budget.status = "Submitted"
		self.budget.save(ignore_permissions=True)
		self.budget.status = "Approved"
		self.budget.save(ignore_permissions=True)
		self.budget.reload()

	# ── A2: Budget header new fields ──────────────────────────────────────────

	def test_a2_budget_has_active_status_option(self):
		"""Budget status field allows 'Active' after Approved."""
		self._budget_to_approved()
		try:
			self.budget.status = "Active"
			self.budget.save(ignore_permissions=True)
		except Exception as e:
			self.fail(f"Setting status to Active raised: {e}")
		self.budget.reload()
		self.assertEqual(self.budget.status, "Active")

	def test_a2_budget_has_closed_status_option(self):
		"""Budget status field allows 'Closed' after Active."""
		self._budget_to_approved()
		self.budget.status = "Active"
		self.budget.save(ignore_permissions=True)
		self.budget.status = "Closed"
		self.budget.save(ignore_permissions=True)
		self.budget.reload()
		self.assertEqual(self.budget.status, "Closed")

	def test_a2_budget_has_revised_status_option(self):
		"""Budget status field allows 'Revised' after Approved."""
		self._budget_to_approved()
		self.budget.status = "Revised"
		self.budget.save(ignore_permissions=True)
		self.budget.reload()
		self.assertEqual(self.budget.status, "Revised")

	def test_a2_budget_governance_fields_can_be_saved(self):
		"""budget_owner, effective_date, closing_date can be set and saved."""
		self.budget.budget_owner   = "Director of Budget"
		self.budget.effective_date = "2026-01-01"
		self.budget.closing_date   = "2026-12-31"
		self.budget.save(ignore_permissions=True)
		self.budget.reload()
		self.assertEqual(self.budget.budget_owner, "Director of Budget")
		self.assertEqual(str(self.budget.effective_date), "2026-01-01")
		self.assertEqual(str(self.budget.closing_date), "2026-12-31")

	# ── A3: Budget Reservation Converted status ───────────────────────────────

	def test_a3_reservation_converted_status_is_valid(self):
		"""Budget Reservation status can be set to Converted."""
		line_name = self.line.name
		res = frappe.get_doc({
			"doctype": "Budget Reservation",
			"budget_line": line_name,
			"budget": self.budget.name,
			"procuring_entity": self.entity,
			"fiscal_year": 2026,
			"source_doctype": "Demand Intake",
			"source_docname": "TEST-DEMAND-001",
			"source_business_id": "D-001",
			"amount": 100_000,
			"currency": "KES",
			"status": "Active",
		}).insert(ignore_permissions=True)

		try:
			res.status = "Converted"
			res.commitment_amount = 96_000
			res.save(ignore_permissions=True)
			res.reload()
			self.assertEqual(res.status, "Converted")
			self.assertAlmostEqual(flt(res.commitment_amount), 96_000, places=2)
		finally:
			frappe.delete_doc("Budget Reservation", res.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	# ── A4: Funding Source new fields ─────────────────────────────────────────

	def test_a4_funding_source_has_source_code_and_type(self):
		"""Funding Source has source_code and source_type fields."""
		h = frappe.generate_hash(length=4)
		fs = frappe.get_doc({
			"doctype": "Funding Source",
			"title": f"Test Source {h}",
			"source_code": f"TS-{h}",
			"source_type": "Exchequer",
			"is_active": 1,
		}).insert(ignore_permissions=True)

		try:
			fs.reload()
			self.assertEqual(fs.source_code, f"TS-{h}")
			self.assertEqual(fs.source_type, "Exchequer")
		finally:
			frappe.delete_doc("Funding Source", fs.name, force=True, ignore_permissions=True)
			frappe.db.commit()
