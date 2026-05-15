# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-03 — doc 8 **TM2-SMOKE-PUB-003**; doc 9 §21.2 ``test_TM2_SMOKE_PUB_003_…``.

**Publish** on an **Approved for Publication** tender must create a **TM2 Publication Record**,
bind **publication snapshot** + output codes on the active **TM2 Tender STD Binding**, set tender
**Published**, lock the **Tender STD Instance**, and append audit **Tender Published** with snapshot
and output refs (doc 8 Expected Result + Expected Audit).

Fixture chain: :class:`Tm2ApprovedForPublicationFixtureChain` (shared with P4-06).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o03_tm2_smoke_pub_003_publish_approved_tender_and_bind_publication_snapshot
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.tests.tm2_publish_fixture_chain import (
	Tm2ApprovedForPublicationFixtureChain,
)


class TestO03Tm2SmokePub003PublishApprovedTenderAndBindPublicationSnapshot(
	Tm2ApprovedForPublicationFixtureChain,
):
	"""Doc 8 TM2-SMOKE-PUB-003 — publish approved tender binds publication snapshot."""

	def test_TM2_SMOKE_PUB_003_publish_approved_tender_and_bind_publication_snapshot(self) -> None:
		"""Approved + STD output refs → publish binds snapshot; audit **Tender Published**."""
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

		tm2 = str(out.get("tm2_tender") or "")
		self.assertTrue(tm2)
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "published_by", "published_at"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Published")
		self.assertEqual(row.get("published_by"), "Administrator")
		self.assertTrue(row.get("published_at"))

		pub_name = str(out.get("tm2_publication_record") or "")
		self.assertTrue(pub_name)
		pr = frappe.get_doc("TM2 Publication Record", pub_name)
		self.assertEqual(pr.status, "Published")
		snap_code = cstr(pr.publication_snapshot_code).strip()
		self.assertTrue(snap_code)
		self.assertEqual(pr.bundle_output_code, f"GB-{tcode}-STUB")
		self.assertEqual(pr.dsm_output_code, f"DSM-{tcode}-STUB")
		self.assertEqual(pr.dom_output_code, f"DOM-{tcode}-STUB")
		self.assertEqual(pr.dem_output_code, f"DEM-{tcode}-STUB")
		self.assertEqual(pr.dcm_output_code, f"DCM-{tcode}-STUB")

		bind = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			["binding_status", "publication_snapshot_code", "tender_std_instance"],
			as_dict=True,
		)
		self.assertEqual(bind.get("binding_status"), "Published")
		self.assertEqual(cstr(bind.get("publication_snapshot_code") or "").strip(), snap_code)

		si = str(bind.get("tender_std_instance") or "")
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
		self.assertEqual(cstr(ev[0].get("publication_snapshot_code") or "").strip(), snap_code)
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertEqual(cstr(pl.get("publication_snapshot_code") or "").strip(), snap_code)
		self.assertEqual(pl.get("bundle_output_code"), f"GB-{tcode}-STUB")
