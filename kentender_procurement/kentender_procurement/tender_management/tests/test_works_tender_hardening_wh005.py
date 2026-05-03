# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-005 — ``Tender Hardening Finding`` + ``hardening_findings`` on tender (doc 5 §11, §7.1).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh005
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_SEVERITY_OPTIONS = "Critical\nHigh\nMedium\nLow\nInfo"
_AREA_OPTIONS = (
	"Works Requirements\nAttachments\nBoQ\nLots\nForms\nDerived Models\n"
	"Audit\nLegacy Lockout\nPlanning Handoff\nSTD Binding"
)

_WH005_CHILD_FIELDS: tuple[tuple[str, str, int, str | None], ...] = (
	("finding_code", "Data", 1, None),
	("severity", "Select", 1, _SEVERITY_OPTIONS),
	("area", "Select", 1, _AREA_OPTIONS),
	("message", "Small Text", 1, None),
	("source_object", "Data", 0, None),
	("resolution_hint", "Small Text", 0, None),
	("blocks_transition", "Check", 0, None),
	("blocking_for", "Data", 0, None),
)

_EXPECTED_AREAS = {
	"Works Requirements",
	"Attachments",
	"BoQ",
	"Lots",
	"Forms",
	"Derived Models",
	"Audit",
	"Legacy Lockout",
	"Planning Handoff",
	"STD Binding",
}


class TestWorksTenderHardeningWh005(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh005_child_meta_fields(self) -> None:
		meta = frappe.get_meta("Tender Hardening Finding")
		self.assertEqual(meta.istable, 1)
		for fieldname, fieldtype, reqd, options in _WH005_CHILD_FIELDS:
			with self.subTest(field=fieldname):
				f = meta.get_field(fieldname)
				self.assertIsNotNone(f, f"missing field {fieldname}")
				self.assertEqual(f.fieldtype, fieldtype)
				self.assertEqual(int(f.reqd or 0), reqd)
				if options is not None:
					self.assertEqual(f.options, options)

	def test_wh005_area_options_match_doc(self) -> None:
		meta = frappe.get_meta("Tender Hardening Finding")
		f = meta.get_field("area")
		self.assertIsNotNone(f)
		self.assertEqual(set((f.options or "").strip().split("\n")), _EXPECTED_AREAS)

	def test_wh005_procurement_tender_has_hardening_findings_table(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		f = meta.get_field("hardening_findings")
		self.assertIsNotNone(f)
		self.assertEqual(f.fieldtype, "Table")
		self.assertEqual(f.options, "Tender Hardening Finding")
		self.assertTrue(f.read_only)

	def test_wh005_append_findings_persist(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-005 Hardening Findings Test"
		doc.tender_reference = "WH005-ROW-001"
		doc.append(
			"hardening_findings",
			{
				"finding_code": "WH-005-F001",
				"severity": "Medium",
				"area": "Derived Models",
				"message": "Placeholder readiness not validated.",
				"source_object": "Tender Derived Model Readiness/Submission",
				"resolution_hint": "Run hardening validation (WH-010).",
				"blocks_transition": 0,
				"blocking_for": "Publication",
			},
		)
		doc.append(
			"hardening_findings",
			{
				"finding_code": "WH-005-F002",
				"severity": "Info",
				"area": "Works Requirements",
				"message": "Second row for multi-row persistence.",
			},
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(len(reloaded.hardening_findings), 2)
			r0 = reloaded.hardening_findings[0]
			self.assertEqual(r0.finding_code, "WH-005-F001")
			self.assertEqual(r0.severity, "Medium")
			self.assertEqual(r0.area, "Derived Models")
			self.assertEqual(r0.message, "Placeholder readiness not validated.")
			self.assertEqual(r0.blocking_for, "Publication")
			r1 = reloaded.hardening_findings[1]
			self.assertEqual(r1.finding_code, "WH-005-F002")
			self.assertEqual(r1.severity, "Info")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
