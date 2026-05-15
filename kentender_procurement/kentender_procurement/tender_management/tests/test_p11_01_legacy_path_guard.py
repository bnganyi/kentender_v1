# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-01 — doc 9 §22.1 + doc 8 TM2-SMOKE-LEGACY-* (AUTH_LEGACY_PATH_DENIED + audit).

**EX-20** (doc 9 §25 final bullet / doc 8 §1 pt 14): ``test_EX_20_*`` — v1 document-as-source flags
denied with **Audit Event** + **P11-03** static TM2 contamination scan clean (same checks as
``make tm2-v1-contamination-audit``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p11_01_legacy_path_guard
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender import (
	load_template_defaults,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.audit.tm2_v1_contamination_scan import (
	format_violations,
	run_tm2_v1_contamination_scan,
)
from kentender_procurement.tender_management.security.legacy_v1_path_guard import (
	collect_legacy_rule_injection_flags,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)


class TestP1101LegacyPathGuard(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	@staticmethod
	def _meta(value: object) -> dict:
		if isinstance(value, dict):
			return value
		if isinstance(value, str) and value.strip():
			try:
				out = frappe.parse_json(value)
			except Exception:
				return {}
			return out if isinstance(out, dict) else {}
		return {}

	def _mk_tender(self) -> str:
		ref = f"P11-01-{frappe.generate_hash(length=8)}"
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "P11-01 Legacy Guard"
		doc.tender_reference = ref
		doc.insert(ignore_permissions=True)
		tn = doc.name
		load_template_defaults(tn)

		def _cleanup() -> None:
			if frappe.db.exists("Procurement Tender", tn):
				frappe.delete_doc("Procurement Tender", tn, force=True, ignore_permissions=True)

		self.addCleanup(_cleanup)
		return tn

	def _latest_denial_audit_for_tender(self, tender_name: str) -> dict | None:
		rows = frappe.get_all(
			"Audit Event",
			filters={"document_type": "Procurement Tender", "document_name": tender_name},
			fields=["name", "metadata", "event_type"],
			order_by="creation desc",
			limit=5,
		)
		for row in rows:
			meta = self._meta(row.get("metadata"))
			if meta.get("denial_code") == DenialCode.AUTH_LEGACY_PATH_DENIED.value:
				return {"name": row["name"], "metadata": meta, "event_type": row.get("event_type")}
		return None

	def test_p11_01_collect_flags_nested_configuration_json(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.configuration_json = json.dumps(
			{"section": {"manual_evaluation_criteria_enabled": True}}
		)
		self.assertEqual(
			collect_legacy_rule_injection_flags(doc),
			["manual_evaluation_criteria_enabled"],
		)

	def test_p11_01_save_denies_manual_submission_flag_with_audit(self) -> None:
		tn = self._mk_tender()
		doc = frappe.get_doc("Procurement Tender", tn)
		cfg = json.loads(doc.configuration_json or "{}")
		cfg["manual_submission_checklist_enabled"] = True
		doc.configuration_json = json.dumps(cfg)
		with self.assertRaises(frappe.ValidationError):
			doc.save()
		row = self._latest_denial_audit_for_tender(tn)
		self.assertTrue(row, "expected Audit Event for AUTH_LEGACY_PATH_DENIED")
		meta = row["metadata"]
		self.assertEqual(meta.get("denial_code"), DenialCode.AUTH_LEGACY_PATH_DENIED.value)
		self.assertEqual(meta.get("result"), "Denied")
		self.assertEqual(meta.get("action_code"), "SAVE_PROCUREMENT_TENDER")
		self.assertIn("Access Denied", meta.get("message") or "")

	def test_p11_01_publish_denies_missing_std_template_with_audit(self) -> None:
		tn = self._mk_tender()
		frappe.db.set_value("Procurement Tender", tn, "std_template", None, update_modified=False)
		with self.assertRaises(frappe.ValidationError):
			PublicationTransactionService.publishTender(tn, actor="Administrator")
		row = self._latest_denial_audit_for_tender(tn)
		self.assertTrue(row)
		meta = row["metadata"]
		self.assertEqual(meta.get("denial_code"), DenialCode.AUTH_LEGACY_PATH_DENIED.value)
		self.assertEqual(meta.get("action_code"), "PUBLISH_TENDER")
		self.assertIn("Access Denied", meta.get("message") or "")

	def test_EX_20_legacy_v1_paths_blocked_audited_and_tm2_surfaces_scan_clean(self) -> None:
		"""Doc 9 §25 — legacy v1 document-as-source paths blocked + audited; TM2 tree free of v1 keys."""
		violations = run_tm2_v1_contamination_scan()
		self.assertFalse(
			violations,
			msg="P11-03 / EX-20 contamination violations:\n" + format_violations(violations),
		)

		tn = self._mk_tender()
		doc = frappe.get_doc("Procurement Tender", tn)
		cfg = json.loads(doc.configuration_json or "{}")
		cfg["manual_submission_checklist_enabled"] = True
		doc.configuration_json = json.dumps(cfg)
		with self.assertRaises(frappe.ValidationError):
			doc.save()
		row = self._latest_denial_audit_for_tender(tn)
		self.assertTrue(row, "expected Audit Event for AUTH_LEGACY_PATH_DENIED")
		meta = row["metadata"]
		self.assertEqual(meta.get("denial_code"), DenialCode.AUTH_LEGACY_PATH_DENIED.value)
		self.assertEqual(meta.get("result"), "Denied")
		self.assertEqual(meta.get("action_code"), "SAVE_PROCUREMENT_TENDER")
		self.assertIn("Access Denied", meta.get("message") or "")
