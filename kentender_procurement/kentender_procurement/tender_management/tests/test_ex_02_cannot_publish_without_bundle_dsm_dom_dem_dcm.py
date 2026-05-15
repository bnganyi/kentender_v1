# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EX-02 — doc 9 §25 exit gate: **cannot publish without Bundle / DSM / DOM / DEM / DCM current**.

``publish_tender`` calls ``_readiness_still_valid_denial`` (same output flags as §9.4/§9.5). Each
``*_current`` flag on the latest **TM2 Publication Readiness** must be truthy or publish returns the
matching denial (doc 8 **TM2-SMOKE-PUB-005** pattern for Bundle; parallel codes for other outputs).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_ex_02_cannot_publish_without_bundle_dsm_dom_dem_dcm
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	_OUTPUT_FLAG_DENIALS,
	_latest_publication_readiness,
)
from kentender_procurement.tender_management.tests.tm2_publish_fixture_chain import (
	Tm2ApprovedForPublicationFixtureChain,
)


def _reset_readiness_outputs_current(*, pr_name: str, bind_name: str) -> None:
	frappe.db.set_value(
		"TM2 Publication Readiness",
		pr_name,
		{
			"readiness_status": "Ready",
			"tm2_tender_std_binding": bind_name,
			"timeline_valid": 1,
			"bundle_current": 1,
			"dsm_current": 1,
			"dom_current": 1,
			"dem_current": 1,
			"dcm_current": 1,
		},
		update_modified=False,
	)


class TestEx02CannotPublishWithoutBundleDsmDomDemDcm(Tm2ApprovedForPublicationFixtureChain):
	def test_EX_02_publish_denied_when_any_std_output_not_current_on_readiness(self) -> None:
		"""Flip each ``*_current`` flag on latest readiness → matching ``AUTH_*_MISSING_OR_STALE``; no publish audit."""
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		tm2 = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2)
		bind_name = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"name",
		)
		self.assertTrue(bind_name)
		read_row = _latest_publication_readiness(str(tm2))
		self.assertTrue(read_row)
		pr_name = str(read_row.get("name") or "").strip()
		self.assertTrue(pr_name)

		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None
		ctx = {"granted_permissions": [spec_p.required_permission]}

		for field, expected in _OUTPUT_FLAG_DENIALS:
			_reset_readiness_outputs_current(pr_name=pr_name, bind_name=str(bind_name))
			frappe.db.set_value(
				"TM2 Publication Readiness",
				pr_name,
				{field: 0},
				update_modified=False,
			)
			frappe.db.commit()

			audit_before = frappe.db.count(
				"TM2 Tender Audit Event",
				{"tm2_tender": tm2, "event_type": "Tender Published"},
			)
			out = publish_tender("Administrator", tcode, context=ctx)
			self.assertFalse(out.get("ok"), (field, out))
			self.assertEqual(out.get("denial_code"), expected.value, field)
			audit_after = frappe.db.count(
				"TM2 Tender Audit Event",
				{"tm2_tender": tm2, "event_type": "Tender Published"},
			)
			self.assertEqual(audit_after, audit_before)

		_reset_readiness_outputs_current(pr_name=pr_name, bind_name=str(bind_name))
		frappe.db.commit()
