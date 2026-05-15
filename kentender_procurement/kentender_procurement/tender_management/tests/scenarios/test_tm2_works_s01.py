# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S01 (Happy Path Works Tender).

Doc 7 §6 uses canonical codes (``TND-MOH-2026-001``, ``PKG-MOH-2026-001``); this module proves the
**§2 expected result** on the P6 published Works harness: publication, sealed bid submission,
closing, opening readiness, evaluation handoff, and contract handoff (service-level chain aligned
with ``test_p7_03_*`` / ``test_p7_04_*``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s01
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
from kentender_procurement.tender_management.services.complete_evaluation_handoff import (
	complete_evaluation_handoff,
)
from kentender_procurement.tender_management.services.create_contract_handoff_reference import (
	create_contract_handoff_reference,
)
from kentender_procurement.tender_management.services.prepare_opening_readiness import (
	prepare_opening_readiness,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_CODE = "TM2-WORKS-S01"


class TestTM2WorksS01Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Happy Path Works Tender")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS01HappyPath(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 / §1.1 — TM2-WORKS-S01 lifecycle (tracker **S-01**)."""

	p6_supplier_fixture_prefix = "S01"

	def setUp(self) -> None:
		super().setUp()
		self._p602_suppliers_created: list[str] = []

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

	def _ctx(self, action_code: str) -> dict:
		spec = spec_for_action(action_code)
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

	def test_S_01_happy_path_publication_through_contract_handoff(self) -> None:
		"""Doc 7 §2 — successful publication, submission, opening readiness, evaluation + contract handoff."""
		tcode, tm2, sup = self._published_with_supplier()
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Published")
		self.assertTrue(frappe.db.get_value("TM2 Tender", tm2, "procurement_package"))

		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		sub = submit_bid(
			"Administrator",
			tcode,
			sup,
			_valid_bid_for_fixture(tcode, sup, str(si)),
			context={**self._ctx("BID2_SUBMIT"), "acting_supplier": sup},
		)
		self.assertTrue(sub.get("ok"), sub)

		self._past_deadline(tm2)
		out_c = close_tender("Administrator", tcode, context=self._ctx("CLS2_CLOSE_TENDER"))
		self.assertTrue(out_c.get("ok"), out_c)

		out_p = prepare_opening_readiness(
			"Administrator",
			tcode,
			context=self._ctx("OR2_PREPARE_OPENING_READINESS"),
		)
		self.assertTrue(out_p.get("ok"), out_p)
		self.assertEqual(out_p.get("tender_status"), "Opening Ready")
		orr_name = str(out_p.get("tm2_opening_readiness_record") or "")
		self.assertTrue(orr_name)
		opn = f"OPN-{tcode}-S01"
		frappe.db.set_value(
			"TM2 Opening Readiness Record",
			orr_name,
			{"opening_record_code": opn},
			update_modified=False,
		)
		bid_name = frappe.db.get_value("TM2 Bid Submission", {"tm2_tender": tm2}, "name")
		self.assertTrue(bid_name)
		frappe.db.set_value("TM2 Bid Submission", bid_name, {"bid_status": "Opened"}, update_modified=False)
		frappe.db.set_value("TM2 Tender", tm2, {"status": "Opening Completed"}, update_modified=False)

		out_e = complete_evaluation_handoff(
			"Administrator",
			tcode,
			opn,
			context=self._ctx("EV2_PREPARE_EVALUATION_HANDOFF"),
		)
		self.assertTrue(out_e.get("ok"), out_e)
		self.assertEqual(out_e.get("tender_status"), "Evaluation Ready")
		self.assertEqual(out_e.get("evaluation_handoff_code"), f"EHR-{tcode}")
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Evaluation Ready")

		frappe.db.set_value("TM2 Tender", tm2, {"status": "Awarded"}, update_modified=False)
		award_code = f"AWD-{tcode}-S01"
		out_h = create_contract_handoff_reference(
			"Administrator",
			tcode,
			award_code,
			context={
				**self._ctx("CON2_CREATE_CONTRACT_HANDOFF"),
				"award": {
					"award_decision_code": award_code,
					"awarded_supplier": sup,
					"final_evaluated_price": 96_754_000,
					"currency": "KES",
					"final_boq_reference": f"BOQ-{tcode}-CORRECTED-01",
				},
			},
		)
		self.assertTrue(out_h.get("ok"), out_h)
		self.assertEqual(out_h.get("tender_status"), "Contract Handoff Completed")
		self.assertEqual(out_h.get("contract_handoff_code"), f"CHR-{tcode}")
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Contract Handoff Completed")

		aud_types = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2},
			pluck="event_type",
		)
		self.assertIn("Tender Published", aud_types)
		self.assertIn("Bid Submitted", aud_types)
		self.assertIn("Contract Handoff Reference Created", aud_types)
