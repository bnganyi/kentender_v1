# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S05 (Late Submission Rejection).

**§2:** server-time deadline — late ``submit_bid`` is rejected, **TM2 Late Submission Attempt** recorded,
**Late Submission Rejected** audit. Aligns with doc 9 §11.6 / **EX-14** /
``test_p6_06_record_late_submission_attempt``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s05
"""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	scenario_by_code,
	scenario_tracker_slug,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_CODE = "TM2-WORKS-S05"


class TestTM2WorksS05Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Late Submission Rejection")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS05LateSubmission(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 — TM2-WORKS-S05 (tracker **S-05**). Chain aligned with ``test_p6_06_record_late_submission_attempt``."""

	p6_supplier_fixture_prefix = "S05"

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
		)

	def setUp(self) -> None:
		super().setUp()
		self._p602_suppliers_created: list[str] = []

	def _portal_submit_ctx(self) -> dict:
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_S_05_submit_bid_after_deadline_records_late_attempt_audited_no_bid(self) -> None:
		"""Post-deadline ``submit_bid`` → ``AUTH_DEADLINE_PASSED`` + late row + audit; no bid row."""
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		ctx = {**self._portal_submit_ctx(), "acting_supplier": sup}
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)
		bid_count_before = frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup})
		late_count_before = frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2, "supplier": sup})
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		out = submit_bid("Administrator", tcode, sup, bid, context=ctx)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DEADLINE_PASSED.value)
		self.assertTrue(out.get("late_attempt"))
		self.assertTrue(out.get("late_attempt_code"))
		self.assertEqual(
			bid_count_before,
			frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup}),
		)
		self.assertEqual(
			late_count_before + 1,
			frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2, "supplier": sup}),
		)
		late_name = str(out.get("late_attempt"))
		self.assertTrue(frappe.db.exists("TM2 Late Submission Attempt", late_name))
		meta = frappe.db.get_value("TM2 Late Submission Attempt", late_name, "attempted_payload_metadata")
		if isinstance(meta, str):
			meta = json.loads(meta or "{}")
		self.assertIsInstance(meta, dict)
		self.assertIn("dsm_output_code", meta)
		aud = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Late Submission Rejected",
				"related_object_id": late_name,
			},
			pluck="name",
		)
		self.assertEqual(len(aud), 1)
		self.assertEqual(
			frappe.db.get_value("TM2 Tender Audit Event", aud[0], "denial_code"),
			DenialCode.AUTH_DEADLINE_PASSED.value,
		)
