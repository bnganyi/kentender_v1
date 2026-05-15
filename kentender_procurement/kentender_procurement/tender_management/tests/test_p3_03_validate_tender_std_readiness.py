# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-03 — doc 9 §8.2 ``validate_tender_std_readiness`` (blocker contract + flags).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_03_validate_tender_std_readiness
"""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	validateTenderStdReadiness,
	validate_tender_std_readiness,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.readiness import BLOCKER_ORDER
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP303ValidateTenderStdReadiness(_P401Tm2Cleanup):
	def _mk_tm2_with_std_instance(self) -> tuple[str, str]:
		"""Return ``(tender_code, tender_std_instance_name)``."""
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
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		bout = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertTrue(bout.get("ok"), bout)
		si = str(bout.get("tender_std_instance") or "")
		self.assertTrue(si)
		return tcode, si

	def _assert_blocker_rows_contract(self, blockers: object) -> None:
		self.assertIsInstance(blockers, list)
		for b in blockers:
			self.assertIsInstance(b, dict)
			self.assertIn("code", b)
			self.assertIn("message", b)
			self.assertIsInstance(b.get("code"), str)
			self.assertIsInstance(b.get("message"), str)

	def _assert_blockers_follow_catalog_order(self, blockers: list) -> None:
		order_index = {c: i for i, c in enumerate(BLOCKER_ORDER)}
		last = -1
		for b in blockers:
			code = str(b.get("code") or "")
			if code not in order_index:
				continue
			idx = order_index[code]
			self.assertGreaterEqual(
				idx,
				last,
				msg=f"Blocker {code!r} breaks BLOCKER_ORDER monotonicity after index {last}",
			)
			last = idx

	def test_p3_03_instance_not_found_envelope(self) -> None:
		out = validate_tender_std_readiness("")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("status"), "Blocked")
		self._assert_blocker_rows_contract(out.get("blockers"))
		self.assertEqual((out.get("blockers") or [{}])[0].get("code"), "INSTANCE_NOT_FOUND")
		for k in ("bundle_current", "dsm_current", "dom_current", "dem_current", "dcm_current"):
			self.assertIs(out.get(k), False)

	def test_p3_03_unknown_instance_not_found(self) -> None:
		out = validate_tender_std_readiness("STDINST-NONEXISTENT-P303-99999")
		self.assertFalse(out.get("ok"))
		self.assertEqual((out.get("blockers") or [{}])[0].get("code"), "INSTANCE_NOT_FOUND")

	def test_p3_03_blocked_fixture_blockers_and_flags(self) -> None:
		_tcode, si = self._mk_tm2_with_std_instance()
		out = validate_tender_std_readiness(si)
		self.assertTrue(out.get("ok"), msg="Adapter ok=True when evaluation runs (Blocked is not a transport error).")
		self.assertEqual(out.get("status"), "Blocked")
		self.assertEqual(out.get("instance"), si)
		blockers = out.get("blockers") or []
		self._assert_blocker_rows_contract(blockers)
		self._assert_blockers_follow_catalog_order(blockers)
		codes = [str(b.get("code") or "") for b in blockers]
		self.assertIn("DEM_MISSING", codes)
		self.assertFalse(out.get("dem_current"))

	def test_p3_03_camel_case_alias_matches_snake(self) -> None:
		a = validate_tender_std_readiness("")
		b = validateTenderStdReadiness("")
		self.assertEqual(a, b)

	def test_p3_03_ready_path_shape_via_evaluate_patch(self) -> None:
		_tcode, si = self._mk_tm2_with_std_instance()
		fake_eval = {
			"status": "Ready",
			"blockers": [],
			"warnings": [],
			"instance": si,
		}
		with patch(
			"kentender_procurement.tender_management.services.tm2_std_adapter.StdInstanceReadinessService.evaluate",
			return_value=fake_eval,
		):
			out = validate_tender_std_readiness(si)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("status"), "Ready")
		self.assertEqual(out.get("blockers"), [])
		self.assertTrue(out.get("bundle_current"))
		self.assertTrue(out.get("dsm_current"))
		self.assertTrue(out.get("dom_current"))
		self.assertTrue(out.get("dem_current"))
		self.assertTrue(out.get("dcm_current"))
