# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S07 (Tender Cancellation Before Closing).

**§2:** cancellation while tender is still **Published** (before closing) — governed ``cancel_tender``,
audit **Tender Cancelled**, and **no further bid submissions** (``submit_bid`` requires **Published**).
Aligns with **P4-08** / ``cancel_tender`` and **P6-05** ``submit_bid`` state gate.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s07
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
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.services.tm2_cancel_supersede_retender import cancel_tender
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_CODE = "TM2-WORKS-S07"


class TestTM2WorksS07Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Tender Cancellation Before Closing")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS07CancelBeforeClose(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 — TM2-WORKS-S07 (tracker **S-07**)."""

	p6_supplier_fixture_prefix = "S07"

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

	def _cancel_ctx(self) -> dict:
		spec = spec_for_action("TND2_CANCEL")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _portal_submit_ctx(self) -> dict:
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_S_07_cancel_published_tender_audits_and_blocks_further_bid_submission(self) -> None:
		"""Published (pre-close) → ``cancel_tender`` → **Tender Cancelled**; ``submit_bid`` denied."""
		tcode, tm2, sup = self._published_with_supplier()
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Published")

		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)

		reason = "Procurement cancelled before bid closing per S-07 scenario (cabinet re-prioritisation)."
		out = cancel_tender("Administrator", tcode, reason, context=self._cancel_ctx())
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Cancelled")

		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "is_active", "cancellation_reason"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Cancelled")
		self.assertEqual(int(row.get("is_active") or 0), 0)
		self.assertTrue(row.get("cancellation_reason"))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Cancelled"},
			fields=["reason", "previous_state", "new_state"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("new_state"), "Cancelled")
		self.assertEqual(ev[0].get("previous_state"), "Published")

		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		sub = submit_bid(
			"Administrator",
			tcode,
			sup,
			bid,
			context={**self._portal_submit_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(sub.get("ok"), sub)
		self.assertEqual(sub.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)
