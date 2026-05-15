# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S10 (Addendum Acknowledgement Failure).

**§2:** issued addendum with ``requires_supplier_acknowledgement`` and no supplier acknowledgement —
``start_bid_draft`` and ``submit_bid`` deny with ``AUTH_ADDENDUM_ACK_REQUIRED`` (doc 9 §11.2 / §11.5;
**TM2-BID-GOV-003**). Doc-7 **expected_result** also says *audited*; successful-path bid audits (**Bid Submitted**)
do not run on this early deny (no **TM2 Bid Submission** row); optional **Addendum Issued** audit is out of
scope for this fixture (manual **Issued** row like **P6-02** / **P10-07**).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s10
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
from kentender_procurement.tender_management.services.start_bid_draft import start_bid_draft
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_CODE = "TM2-WORKS-S10"


class TestTM2WorksS10Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Addendum Acknowledgement Failure")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS10AcknowledgementGate(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 — TM2-WORKS-S10 (tracker **S-10**)."""

	p6_supplier_fixture_prefix = "S10"

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

	def _portal_draft_ctx(self) -> dict:
		spec_s = spec_for_action("BID2_START_DRAFT")
		spec_v = spec_for_action("BID2_SAVE_DRAFT")
		self.assertIsNotNone(spec_s)
		self.assertIsNotNone(spec_v)
		assert spec_s is not None and spec_v is not None
		return {"granted_permissions": [spec_s.required_permission, spec_v.required_permission]}

	def _portal_submit_ctx(self) -> dict:
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _issued_addendum_requiring_ack(self, tm2: str) -> str:
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "S-10 acknowledgement gate",
				"reason": "Fixture for TM2-WORKS-S10 — missing supplier acknowledgement blocks bid prep/submit.",
				"requires_supplier_acknowledgement": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Addendum", ad.name, "status", "Issued", update_modified=False)
		return str(ad.name)

	def test_S_10_missing_addendum_ack_blocks_start_draft_and_submit_bid(self) -> None:
		"""**Issued** addendum + ``requires_supplier_acknowledgement`` → ``AUTH_ADDENDUM_ACK_REQUIRED``; no bid."""
		tcode, tm2, sup = self._published_with_supplier()
		self._issued_addendum_requiring_ack(tm2)

		ctx_draft = {**self._portal_draft_ctx(), "acting_supplier": sup}
		out_draft = start_bid_draft("Administrator", tcode, sup, context=ctx_draft)
		self.assertFalse(out_draft.get("ok"), out_draft)
		self.assertEqual(out_draft.get("denial_code"), DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value)

		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		ctx_sub = {**self._portal_submit_ctx(), "acting_supplier": sup}
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		bid_before = frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup})
		out_sub = submit_bid("Administrator", tcode, sup, bid, context=ctx_sub)
		self.assertFalse(out_sub.get("ok"), out_sub)
		self.assertEqual(out_sub.get("denial_code"), DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value)
		self.assertTrue(out_sub.get("pending_addendum_codes"))
		self.assertEqual(
			bid_before,
			frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup}),
		)
