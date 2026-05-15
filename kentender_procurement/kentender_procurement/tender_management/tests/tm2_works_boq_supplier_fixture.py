# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Published TM2 + Works **Tender STD Instance BOQ** for ``validate_works_boq_payload`` tests.

Plain **mixin** (does not subclass ``IntegrationTestCase``) so unittest does not collect it as a
test class. On concrete classes, list this mixin **first** in the bases tuple so ``setUpClass``
runs before ``IntegrationTestCase`` (otherwise ``upsert_std_template`` never runs).
Mix with ``_P401Tm2Cleanup``, ``P6PublishedTm2Fixture`` — e.g.
``class Tests(Tm2WorksBoqSupplierFixture, _P401Tm2Cleanup, P6PublishedTm2Fixture):``.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService, get_boq_for_instance
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService


class Tm2WorksBoqSupplierFixture:
	"""Published tender + supplier + SI Works BOQ rows (items 1.1 qty 100, 1.2 provisional)."""

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		# Parallel test modules can race on ``STD Template``; retry after DB rollback.
		for attempt in range(5):
			try:
				upsert_std_template()
				break
			except frappe.TimestampMismatchError:
				if attempt == 4:
					raise
				frappe.db.rollback()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
		)

	def setUp(self) -> None:
		super().setUp()
		self._p602_suppliers_created: list[str] = []

	def _published_si_supplier_boq(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		assert si
		si = str(si)
		frappe.db.set_value(
			"Tender STD Instance",
			si,
			{"procurement_category": "WORKS"},
			update_modified=False,
		)
		existing = get_boq_for_instance(si)
		if existing:
			frappe.delete_doc("Tender STD Instance BOQ", existing.name, force=True, ignore_permissions=True)
		boq = StdInstanceBoqService.create_boq_for_instance(
			si, currency="KES", ignore_boq_publication_lock=True
		)
		boq = StdInstanceBoqService.add_bill(
			boq.name, "B1", "Lot 1", "Works", ignore_boq_publication_lock=True
		)
		bill_code = (boq.boq_bills or [])[0].bill_instance_code
		StdInstanceBoqService.add_item(
			boq.name,
			bill_code,
			"1.1",
			"Measured work",
			"m2",
			100.0,
			item_type="Normal",
			supplier_input_mode="Rate Only",
			rate_required_from_supplier=True,
			status="Published",
			ignore_boq_publication_lock=True,
		)
		StdInstanceBoqService.add_item(
			boq.name,
			bill_code,
			"1.2",
			"Provisional allowance",
			"nr",
			1.0,
			item_type="Provisional Sum",
			supplier_input_mode="Fixed Amount",
			rate_required_from_supplier=False,
			fixed_amount=5000.0,
			status="Published",
			ignore_boq_publication_lock=True,
		)
		frappe.db.set_value(
			"Tender STD Instance BOQ",
			boq.name,
			"status",
			"Published",
			update_modified=False,
		)
		d_new = StdInstanceGeneratedOutputService.generate_dsm(si, ignore_generated_output_lock=True)
		StdInstanceGeneratedOutputService.publish_output(
			d_new.name, ignore_generated_output_immutability=True
		)
		assert (
			cstr(frappe.db.get_value("Tender STD Instance", si, "procurement_category") or "").upper() == "WORKS"
		)
		return tcode, tm2, sup, si

	def _valid_lines(self) -> list[dict]:
		return [
			{"item_number": "1.1", "rate": 10.0},
			{"item_number": "1.2"},
		]
