# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-06 — doc 9 §9.6 ``publish_tender``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_06_publish_tender
"""

from __future__ import annotations

import json

import frappe
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.tests.tm2_publish_fixture_chain import (
	Tm2ApprovedForPublicationFixtureChain,
)


class TestP406PublishTender(Tm2ApprovedForPublicationFixtureChain):
	def test_p4_06_success_publication_record_audit_notification(self) -> None:
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
		self.assertEqual(out.get("status"), "Published")
		tm2 = out.get("tm2_tender")
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "published_by", "published_at"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Published")
		self.assertEqual(row.get("published_by"), "Administrator")
		self.assertTrue(row.get("published_at"))

		pub = out.get("tm2_publication_record")
		self.assertTrue(pub)
		pr = frappe.get_doc("TM2 Publication Record", pub)
		self.assertEqual(pr.status, "Published")
		self.assertTrue(pr.publication_snapshot_code)
		self.assertEqual(pr.bundle_output_code, f"GB-{tcode}-STUB")

		bind = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			["binding_status", "publication_snapshot_code"],
			as_dict=True,
		)
		self.assertEqual(bind.get("binding_status"), "Published")
		self.assertTrue(bind.get("publication_snapshot_code"))

		si = frappe.db.get_value("TM2 Tender STD Binding", {"tm2_tender": tm2, "is_active": 1}, "tender_std_instance")
		self.assertEqual(
			frappe.db.get_value("Tender STD Instance", si, "instance_status"),
			"Published Locked",
		)

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Published"},
			fields=["event_payload", "publication_snapshot_code"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertTrue(ev[0].get("publication_snapshot_code"))
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertTrue(pl.get("publication_snapshot_code"))
		self.assertEqual(pl.get("bundle_output_code"), f"GB-{tcode}-STUB")

		ntf = frappe.get_all(
			"TM2 Notification Record",
			filters={"tm2_tender": tm2, "notification_type": "Publication"},
			limit=1,
		)
		self.assertEqual(len(ntf), 1)

	def test_p4_06_snapshot_missing_denied(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=False)
		spec_p = spec_for_action("TND2_PUBLISH")
		assert spec_p is not None
		out = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value)

	def test_p4_06_wrong_status_denied(self) -> None:
		self._ensure_std_bindable()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		assert spec_c is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "")
		spec_p = spec_for_action("TND2_PUBLISH")
		assert spec_p is not None
		pout = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertFalse(pout.get("ok"))
		self.assertEqual(pout.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p4_06_auth_denied(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		out = publish_tender("Administrator", tcode, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_06_second_publish_denied(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		spec_p = spec_for_action("TND2_PUBLISH")
		assert spec_p is not None
		ctx = {"granted_permissions": [spec_p.required_permission]}
		out1 = publish_tender("Administrator", tcode, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = publish_tender("Administrator", tcode, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)
