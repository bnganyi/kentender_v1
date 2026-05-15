# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EX-01 — doc 9 §25 exit gate: **cannot publish without STD binding**.

``publish_tender`` must refuse when there is no **active** ``TM2 Tender STD Binding`` for the tender
(doc 9 §9.6 / ``publish_tender.py``). Denial: ``STD_AUTH_OBJECT_SCOPE_DENIED`` (aligns with doc 8
publication hardening: no controlling binding → no publish).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_ex_01_cannot_publish_without_std_binding
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


class TestEx01CannotPublishWithoutStdBinding(Tm2ApprovedForPublicationFixtureChain):
	def test_EX_01_publish_denied_when_no_active_std_binding(self) -> None:
		"""Approved + outputs, then all bindings deactivated → publish denied; no Tender Published audit."""
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		tm2 = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2)
		binds = frappe.get_all(
			"TM2 Tender STD Binding",
			filters={"tm2_tender": tm2},
			pluck="name",
		)
		self.assertTrue(binds)
		for bn in binds:
			frappe.db.set_value(
				"TM2 Tender STD Binding",
				bn,
				{"is_active": 0},
				update_modified=False,
			)
		frappe.db.commit()

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
		self.assertEqual(out.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value)
		audit_after = frappe.db.count(
			"TM2 Tender Audit Event",
			{"tm2_tender": tm2, "event_type": "Tender Published"},
		)
		self.assertEqual(audit_after, audit_before)
