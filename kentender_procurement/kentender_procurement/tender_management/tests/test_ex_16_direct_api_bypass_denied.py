# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EX-16 — doc 9 §25 / TM2-NB-016: direct **TM2 Tender** ``save()`` cannot set **Published** (bypass).

Governed publication remains ``publish_tender`` (``frappe.db.set_value`` on status after checks).
``TM2 Tender`` controller: ``flags.ignore_tm2_tender_governed_status_mutation`` for controlled tests.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_ex_16_direct_api_bypass_denied
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.tests.tm2_publish_fixture_chain import Tm2ApprovedForPublicationFixtureChain
from frappe.tests import IntegrationTestCase


class TestEx16DirectApiBypassDenied(Tm2ApprovedForPublicationFixtureChain, IntegrationTestCase):
	def test_EX_16_direct_document_save_cannot_set_published_bypassing_publish_service(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		tm2_name = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2_name)
		doc = frappe.get_doc("TM2 Tender", tm2_name)
		doc.status = "Published"
		with self.assertRaises(frappe.ValidationError) as ar:
			doc.save(ignore_permissions=True)
		self.assertIn(DenialCode.AUTH_ACTION_AVAILABILITY_DENIED.value, str(ar.exception))

	def test_EX_16_publish_tender_service_still_updates_status_via_governed_path(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None
		out = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(
			frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "status"),
			"Published",
		)
