# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-02 — doc 9 §13.3 ``export_tender_evidence`` / ``exportTenderEvidence``.

**EX-19** (doc 9 §25 / doc 8 TM2-SMOKE-AUD-002): ``test_EX_19_*`` — evidence export links package → tender →
STD binding → publication snapshots/records → bid submission, with audit **Tender Published** /
**Bid Submitted** / **Bid Sealed** (addendum / closing / opening / evaluation / contract slots present
when those DocTypes exist).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p8_02_export_tender_evidence
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.export_tender_evidence import (
	EVIDENCE_EXPORT_SECTION_KEYS,
	exportTenderEvidence,
	export_tender_evidence,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP802ExportTenderEvidence(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P802"

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

	def _export_ctx(self) -> dict:
		spec = spec_for_action("AUD2_EXPORT_EVIDENCE")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _portal_submit_ctx(self) -> dict:
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_p8_02_alias_matches_snake(self) -> None:
		out1 = export_tender_evidence("Administrator", "TND-NONEXISTENT-P802-ALIAS", context={})
		out2 = exportTenderEvidence("Administrator", "TND-NONEXISTENT-P802-ALIAS", context={})
		self.assertEqual(out1, out2)

	def test_p8_02_permission_denied_without_export_perm(self) -> None:
		tcode, _tm2, _sup = self._published_with_supplier()
		out = export_tender_evidence("Administrator", tcode, context={})
		self.assertFalse(out.get("ok"))
		self.assertTrue(out.get("denial_code"))

	def test_p8_02_section_keys_and_package_lineage(self) -> None:
		tcode, tm2, _sup = self._published_with_supplier()
		out = export_tender_evidence("Administrator", tcode, context=self._export_ctx())
		self.assertTrue(out.get("ok"), out)
		for k in EVIDENCE_EXPORT_SECTION_KEYS:
			self.assertIn(k, out, f"missing export section {k!r}")
		pl = out.get("package_lineage") or {}
		self.assertIn("procurement_package", pl)
		self.assertIn("tm2_lineage_fields", pl)
		self.assertEqual(out.get("tender_lifecycle", {}).get("tm2_tender", {}).get("tender_code"), tcode)
		self.assertIsInstance(out.get("audit_trail"), list)
		self.assertGreaterEqual(len(out["audit_trail"]), 1)
		flags = out.get("export_flags") or {}
		self.assertFalse(flags.get("sealed_bid_content_included"))

	def test_p8_02_pre_opening_redacts_bid_components_even_if_confidential_requested(self) -> None:
		tcode, tm2, sup = self._published_with_supplier()[:3]
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		sub = submit_bid(
			"Administrator",
			tcode,
			sup,
			bid,
			context={**self._portal_submit_ctx(), "acting_supplier": sup},
		)
		self.assertTrue(sub.get("ok"), sub)
		bid_name = str(sub.get("bid_submission") or "")
		n_comp = frappe.db.count("TM2 Bid Submission Component", {"tm2_bid_submission": bid_name})
		self.assertGreater(n_comp, 0)

		out = export_tender_evidence(
			"Administrator",
			tcode,
			include_confidential=True,
			context=self._export_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		self.assertFalse((out.get("export_flags") or {}).get("sealed_bid_content_included"))
		for row in out.get("bid_submission_components") or []:
			self.assertTrue(row.get("sealed_bid_fields_redacted"))
			self.assertNotIn("validation_payload", row)
			self.assertNotIn("file_ref", row)

	def test_p8_02_post_opening_include_confidential_exposes_components(self) -> None:
		tcode, tm2, sup = self._published_with_supplier()[:3]
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		sub = submit_bid(
			"Administrator",
			tcode,
			sup,
			bid,
			context={**self._portal_submit_ctx(), "acting_supplier": sup},
		)
		self.assertTrue(sub.get("ok"), sub)
		frappe.db.set_value("TM2 Tender", tm2, {"status": "Opening Completed"}, update_modified=False)
		out = export_tender_evidence(
			"Administrator",
			tcode,
			include_confidential=True,
			context=self._export_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		self.assertTrue((out.get("export_flags") or {}).get("sealed_bid_content_included"))
		found_payload = False
		for row in out.get("bid_submission_components") or []:
			if row.get("validation_payload"):
				found_payload = True
				break
		self.assertTrue(found_payload, "expected at least one component with validation_payload after opening")

	def test_p8_02_sensitive_denials_include_access_denied_shape(self) -> None:
		tcode, tm2, _sup = self._published_with_supplier()
		frappe.get_doc(
			{
				"doctype": "TM2 Tender Audit Event",
				"tm2_tender": tm2,
				"tender_code": tcode,
				"event_type": "Access Denied",
				"actor_type": "User",
				"actor_user": "Administrator",
				"denial_code": "AUTH_SEALED_BID_DENIED",
				"event_payload": {"attempted_action": "view_bid"},
			}
		).insert(ignore_permissions=True)
		out = export_tender_evidence("Administrator", tcode, context=self._export_ctx())
		self.assertTrue(out.get("ok"), out)
		sens = out.get("sensitive_denial_events") or []
		codes = {str(x.get("denial_code") or "") for x in sens}
		self.assertIn("AUTH_SEALED_BID_DENIED", codes)

	def test_EX_19_export_supports_doc8_lifecycle_reconstruction_chain(self) -> None:
		"""Doc 9 §25 / doc 8 TM2-SMOKE-AUD-002 — §13.3 export stitches procurement → tender → STD → publish → bid."""
		tcode, tm2, sup = self._published_with_supplier()[:3]
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		sub = submit_bid(
			"Administrator",
			tcode,
			sup,
			bid,
			context={**self._portal_submit_ctx(), "acting_supplier": sup},
		)
		self.assertTrue(sub.get("ok"), sub)

		out = export_tender_evidence("Administrator", tcode, context=self._export_ctx())
		self.assertTrue(out.get("ok"), out)
		for k in EVIDENCE_EXPORT_SECTION_KEYS:
			self.assertIn(k, out, k)

		tm2_row = frappe.get_doc("TM2 Tender", tm2)
		pl = out.get("package_lineage") or {}
		pkg = pl.get("procurement_package") or {}
		self.assertEqual(pkg.get("name"), tm2_row.procurement_package)

		active = (out.get("std_binding") or {}).get("active") or {}
		self.assertTrue(active.get("name"))
		self.assertEqual(
			cstr(active.get("tender_std_instance") or "").strip(),
			cstr(si).strip(),
		)

		snaps = out.get("publication_snapshots") or []
		self.assertTrue(snaps)
		pub_codes = {cstr(s.get("publication_snapshot_code") or "").strip() for s in snaps}
		self.assertTrue(bool(pub_codes - {""}))

		pubs = out.get("publication_records") or []
		self.assertGreaterEqual(len(pubs), 1)

		bids = out.get("bid_submissions") or []
		self.assertGreaterEqual(len(bids), 1)
		self.assertEqual(cstr(bids[0].get("tender_code") or "").strip(), tcode)

		types = {cstr(r.get("event_type") or "").strip() for r in (out.get("audit_trail") or [])}
		self.assertIn("Tender Published", types)
		self.assertIn("Bid Submitted", types)
		self.assertIn("Bid Sealed", types)

		self.assertIsInstance(out.get("addendum_history"), list)
		for opt_key in (
			"tender_closing_record",
			"opening_readiness_record",
			"evaluation_handoff_record",
			"contract_handoff_reference",
		):
			val = out.get(opt_key)
			self.assertTrue(val is None or isinstance(val, dict), opt_key)
