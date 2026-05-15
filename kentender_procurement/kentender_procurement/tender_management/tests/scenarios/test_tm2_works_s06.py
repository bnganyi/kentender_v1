# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S06 (No Valid Submissions / Retender).

**§2:** after deadline, **no valid bids** → ``close_tender`` yields **Closed - No Valid Submissions**;
governed **retender** path via ``mark_retender_required``. Aligns with **P7-01**
``test_p7_01_close_no_valid_submissions`` and **P4-08** ``test_p4_08_mark_retender_from_closed_no_valid``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s06
"""

from __future__ import annotations

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
from kentender_procurement.tender_management.services.close_tender import close_tender
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.tm2_cancel_supersede_retender import mark_retender_required
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)

_CODE = "TM2-WORKS-S06"


class TestTM2WorksS06Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "No Valid Submissions")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS06CloseNoBidsRetender(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 — TM2-WORKS-S06 (tracker **S-06**)."""

	p6_supplier_fixture_prefix = "S06"

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

	def _close_ctx(self) -> dict:
		spec = spec_for_action("CLS2_CLOSE_TENDER")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _mark_retender_ctx(self) -> dict:
		spec = spec_for_action("TND2_MARK_RETENDER_REQUIRED")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _past_deadline(self, tm2: str) -> None:
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)

	def test_S_06_close_no_valid_submissions_then_mark_retender_required(self) -> None:
		"""Published tender, deadline passed, zero bids → close → **Retender Required**."""
		tcode, tm2, _sup, _si = self._published_si_supplier()
		self._past_deadline(tm2)

		out_close = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertTrue(out_close.get("ok"), out_close)
		self.assertEqual(out_close.get("tender_status"), "Closed - No Valid Submissions")
		self.assertEqual(out_close.get("valid_submission_count"), 0)
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Closed - No Valid Submissions")

		cl = frappe.get_doc("TM2 Tender Closing Record", out_close.get("tm2_tender_closing_record"))
		self.assertEqual(cl.closing_status, "Closed With No Valid Submissions")
		self.assertEqual(int(cl.no_valid_submissions or 0), 1)

		ev_close = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Closed"},
			pluck="name",
		)
		self.assertEqual(len(ev_close), 1)

		out_mr = mark_retender_required(
			"Administrator",
			tcode,
			"No compliant bids received; retender with revised eligibility (S-06).",
			context=self._mark_retender_ctx(),
		)
		self.assertTrue(out_mr.get("ok"), out_mr)
		self.assertEqual(out_mr.get("status"), "Retender Required")

		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "is_active"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Retender Required")
		self.assertEqual(int(row.get("is_active") or 0), 0)

		ev_mr = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Retender Required"},
			fields=["reason", "previous_state", "new_state"],
			limit=1,
		)
		self.assertEqual(len(ev_mr), 1)
		self.assertEqual(ev_mr[0].get("previous_state"), "Closed - No Valid Submissions")
		self.assertEqual(ev_mr[0].get("new_state"), "Retender Required")

	def _published_si_supplier(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		assert si
		return tcode, tm2, sup, str(si)
