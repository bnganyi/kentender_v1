# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EX-03 — doc 9 §25 exit gate: **cannot publish without publication snapshot binding**.

``publish_tender`` calls ``create_or_get_publication_snapshot_for_tm2``; when the **Tender STD Instance**
has no current Bundle/DSM/DOM/DEM/DCM output codes, the adapter cannot build a snapshot and publish
returns ``AUTH_PUBLICATION_SNAPSHOT_MISSING`` (doc 8 **TM2-SMOKE-PUB-006**; aligns with **O-04** and
``test_p4_06_snapshot_missing_denied``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_ex_03_cannot_publish_without_publication_snapshot
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.tests.tm2_publish_fixture_chain import (
	Tm2ApprovedForPublicationFixtureChain,
)


class TestEx03CannotPublishWithoutPublicationSnapshot(Tm2ApprovedForPublicationFixtureChain):
	def test_EX_03_publish_denied_without_publication_snapshot_binding_path(self) -> None:
		"""Approved tender without STD output refs on instance → ``AUTH_PUBLICATION_SNAPSHOT_MISSING``; no publish audit."""
		tcode = self._mk_approved_for_publication(seed_outputs=False)
		tm2 = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2)

		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None

		audit_before = frappe.db.count(
			"TM2 Tender Audit Event",
			{"tm2_tender": tm2, "event_type": "Tender Published"},
		)
		out = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value)
		audit_after = frappe.db.count(
			"TM2 Tender Audit Event",
			{"tm2_tender": tm2, "event_type": "Tender Published"},
		)
		self.assertEqual(audit_after, audit_before)
