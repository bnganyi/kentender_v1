# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-01 — doc 9 §13.1 ``append_tender_audit_event`` / ``appendTenderAuditEvent`` + §13.2 payload gates.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p8_01_append_tender_audit_event
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.services.append_tender_audit_event import (
	appendTenderAuditEvent,
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP801AppendTenderAuditEvent(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P801"

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

	def _tm2_from_mk(self) -> tuple[str, str]:
		tcode = self._mk_approved_for_publication(seed_outputs=False)
		tm2 = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2)
		self.addCleanup(self._cleanup_tm2, tm2)
		return tcode, str(tm2)

	def _pub_payload(self, tcode: str) -> dict:
		return {
			"tm2_publication_record": "PUB-FIXTURE",
			"publication_snapshot_code": f"PUBSNAP-{tcode}-TM2",
			"bundle_output_code": "GB-FIX",
			"dsm_output_code": "DSM-FIX",
			"dom_output_code": "DOM-FIX",
			"dem_output_code": "DEM-FIX",
			"dcm_output_code": "DCM-FIX",
		}

	def test_p8_01_tender_published_section_13_2_ok(self) -> None:
		tcode, _tm2 = self._tm2_from_mk()
		pl = self._pub_payload(tcode)
		code = append_tender_audit_event(
			tcode,
			"Tender Published",
			"Administrator",
			pl,
			related_object_type="TM2 Publication Record",
			related_object_code="PUB-1",
			previous_state="Approved for Publication",
			new_state="Published",
		)
		self.assertTrue(code.startswith(f"TAE-{tcode}-"))

	def test_p8_01_tender_published_missing_output_denied(self) -> None:
		tcode, _tm2 = self._tm2_from_mk()
		pl = self._pub_payload(tcode)
		del pl["bundle_output_code"]
		with self.assertRaises(frappe.ValidationError):
			append_tender_audit_event(
				tcode,
				"Tender Published",
				"Administrator",
				pl,
				related_object_type="TM2 Publication Record",
				related_object_code="PUB-1",
			)

	def test_p8_01_addendum_issued_section_13_2_ok(self) -> None:
		tcode, _tm2 = self._tm2_from_mk()
		pl = {
			**self._pub_payload(tcode),
			"addendum_code": "ADD-FIX-01",
			"tender_code": tcode,
		}
		code = appendTenderAuditEvent(
			tcode,
			"Addendum Issued",
			"Administrator",
			pl,
			related_object_type="TM2 Addendum",
			related_object_code="ADD-NAME",
		)
		self.assertTrue(code.startswith(f"TAE-{tcode}-"))

	def test_p8_01_addendum_missing_addendum_code_denied(self) -> None:
		tcode, _tm2 = self._tm2_from_mk()
		pl = {**self._pub_payload(tcode), "tender_code": tcode}
		with self.assertRaises(frappe.ValidationError):
			append_tender_audit_event(
				tcode,
				"Addendum Issued",
				"Administrator",
				pl,
				related_object_type="TM2 Addendum",
				related_object_code="ADD-NAME",
			)

	def test_p8_01_enforce_section_13_2_false_skips_output_keys(self) -> None:
		tcode, _tm2 = self._tm2_from_mk()
		pl = {"publication_snapshot_code": f"PUBSNAP-{tcode}-TM2"}
		code = append_tender_audit_event(
			tcode,
			"Tender Published",
			"Administrator",
			pl,
			enforce_section_13_2=False,
		)
		self.assertTrue(code.startswith(f"TAE-{tcode}-"))

	def test_p8_01_append_only_row_not_updatable(self) -> None:
		tcode, _tm2 = self._tm2_from_mk()
		pl = self._pub_payload(tcode)
		name = append_tender_audit_event(
			tcode,
			"Tender Published",
			"Administrator",
			pl,
		)
		doc = frappe.get_doc("TM2 Tender Audit Event", name)
		doc.event_payload = {"mutated": True}
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
