# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-001 — Works hardening parent fields on ``Procurement Tender`` (doc 5 §7).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh001
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender import (
	_WORKS_HARDENING_STATUS_DEFAULT,
	_WORKS_HARDENING_STATUS_FIELDS,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_WH001_FIELDS: tuple[str, ...] = (
	"works_hardening_status",
	"works_hardening_checked_at",
	"works_hardening_validation_json",
	"works_hardening_snapshot_json",
	"works_hardening_snapshot_hash",
	"derived_models_status",
	"boq_hardening_status",
	"works_requirements_status",
	"attachments_status",
)


class TestWorksTenderHardeningWh001(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh001_meta_has_hardening_fields(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		names = {df.fieldname for df in meta.fields}
		for fn in _WH001_FIELDS:
			with self.subTest(field=fn):
				self.assertIn(fn, names)
		for fn in _WORKS_HARDENING_STATUS_FIELDS:
			f = meta.get_field(fn)
			self.assertTrue(f.read_only, f"{fn} must be read-only (doc 5 WH-001)")
			self.assertEqual(f.default, _WORKS_HARDENING_STATUS_DEFAULT)
		for fn in ("works_hardening_validation_json", "works_hardening_snapshot_json"):
			f = meta.get_field(fn)
			self.assertEqual(f.fieldtype, "Code")
			self.assertEqual(f.options, "JSON")
			self.assertTrue(f.read_only)

	def test_wh001_status_defaults_on_insert(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-001 Default Test"
		doc.tender_reference = "WH001-DEF-001"
		doc.insert(ignore_permissions=True)
		try:
			for fn in _WORKS_HARDENING_STATUS_FIELDS:
				with self.subTest(field=fn):
					self.assertEqual(doc.get(fn), _WORKS_HARDENING_STATUS_DEFAULT)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
