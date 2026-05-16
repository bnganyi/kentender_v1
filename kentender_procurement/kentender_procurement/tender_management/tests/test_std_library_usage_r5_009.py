# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-009 — STD catalogue Usage panel binds PLC journey + TM2 tender references."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_templates import get_std_library_template_detail
from kentender_procurement.tender_management.seeds import works_master_std_seed

_WORKS_CATALOG_CODE = works_master_std_seed.STD_TEMPLATE_CODE
_WORKS_PLC_REF = works_master_std_seed.STD_TEMPLATE_VERSION_REF
_WORKS_JOURNEY_CODE = "JRN-MOH-2026-001"


class TestStdLibraryUsageR5009(IntegrationTestCase):
	def test_works_usage_panel_reflects_binding_codes(self):
		has_std = bool(frappe.db.exists("STD Template", {"template_code": _WORKS_CATALOG_CODE}))
		has_j = bool(frappe.db.exists("Procurement Journey", {"journey_code": _WORKS_JOURNEY_CODE}))
		if not has_std:
			self.skipTest("WORKS STD Template catalogue row missing on site.")
		if not has_j:
			self.skipTest("WORKS Procurement Journey seed missing on site.")

		frappe.set_user("Administrator")

		with_out = get_std_library_template_detail(_WORKS_CATALOG_CODE)
		self.assertTrue(with_out.get("ok"), msg=with_out)
		usage = with_out["detail"]["usage"]

		journeys = usage.get("journeys") or []
		self.assertTrue(journeys, msg=usage)
		self.assertEqual(journeys[0].get("journey_code"), _WORKS_JOURNEY_CODE)
		self.assertIn("/desk/plc-procurement-journey/", journeys[0].get("open_route") or "")
		self.assertGreaterEqual(len(usage.get("tenders") or []), 1)
		self.assertGreaterEqual(int(usage.get("summary", {}).get("tenders_using_count", 0)), 1)

	def test_binding_codes_union_includes_plc_version_ref_when_catalogue_known(self):
		from kentender_procurement.tender_management.api.std_library_templates import (
			_plc_binding_codes,
		)

		codes = _plc_binding_codes(_WORKS_CATALOG_CODE, _WORKS_CATALOG_CODE)
		self.assertIn(_WORKS_CATALOG_CODE, codes)
		self.assertIn(_WORKS_PLC_REF, codes)
