# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S02 (STD Readiness Blocked).

**§2:** publication path blocked when **DEM** is missing / not current — tender cannot submit for
publication review. Implementation aligns with doc 8 **TM2-SMOKE-READ-001** /
``test_o01_tm2_smoke_read_001_block_publication_review_when_dem_missing``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s02
"""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	scenario_by_code,
	scenario_tracker_slug,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.tm2_publication_readiness_service import (
	insert_tm2_publication_readiness_record,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)

_CODE = "TM2-WORKS-S02"


class TestTM2WorksS02Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "STD Readiness Blocked")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS02ReadinessBlocked(_P401Tm2Cleanup):
	"""Doc 7 §2 / doc 8 TM2-SMOKE-READ-001 — TM2-WORKS-S02 (tracker **S-02**)."""

	def test_S_02_submit_publication_review_denied_when_dem_not_current(self) -> None:
		"""Latest readiness **Ready** but ``dem_current`` false → cannot enter publication review."""
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_b = spec_for_action("TND2_BIND_STD")
		assert spec_c is not None and spec_b is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "")
		tm2_name = str(out.get("tm2_tender") or "")
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		bout = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertTrue(bout.get("ok"), bout)
		bind_name = str(bout.get("tm2_tender_std_binding") or "")
		self.assertTrue(bind_name)

		insert_tm2_publication_readiness_record(
			tm2_name,
			bind_name,
			readiness_status="Ready",
			std_readiness_status="Ready",
			validation_payload={"blockers": [{"code": "DEM_MISSING_OR_STALE"}]},
			package_lineage_valid=True,
			template_version_active=True,
			std_instance_exists=True,
			parameters_complete=True,
			sections_complete=True,
			bundle_current=True,
			dsm_current=True,
			dom_current=True,
			dem_current=False,
			dcm_current=True,
			timeline_valid=True,
			supplier_access_valid=True,
			unresolved_blocker_count=0,
			warning_count=0,
		)

		spec_s = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		assert spec_s is not None
		sout = submit_tender_for_publication_review(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_s.required_permission]},
		)
		self.assertFalse(sout.get("ok"), sout)
		self.assertEqual(sout.get("denial_code"), DenialCode.AUTH_DEM_MISSING_OR_STALE.value)
		self.assertEqual(sout.get("field"), "dem_current")

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2_name, "event_type": "Tender Submitted for Publication Review"},
		)
		self.assertEqual(len(ev), 0)
