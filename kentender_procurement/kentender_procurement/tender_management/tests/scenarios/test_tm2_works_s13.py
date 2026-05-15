# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S13 (Legacy Manual Rule Injection Denial).

**§2:** v1-style manual submission / opening / evaluation rule injection must be **impossible** on governed
surfaces — ``AUTH_LEGACY_PATH_DENIED`` + **Audit Event** on blocked **Procurement Tender** mutations
(doc 9 §22.1 **P11-01**; doc 8 **TM2-SMOKE-LEGACY** / **EX-20**); **P11-03** static scan proves TM2 tree has no
reachable v1 contamination keys.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s13
"""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender import (
	load_template_defaults,
)
from kentender_procurement.tender_management.audit.tm2_v1_contamination_scan import (
	format_violations,
	run_tm2_v1_contamination_scan,
)
from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	scenario_by_code,
	scenario_tracker_slug,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)

_CODE = "TM2-WORKS-S13"


class TestTM2WorksS13Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Legacy Manual Rule Injection Denial")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS13LegacyManualRuleDenial(IntegrationTestCase):
	"""Doc 7 §2 — TM2-WORKS-S13 (tracker **S-13**). Aligned with ``test_p11_01_legacy_path_guard`` / **EX-20**."""

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
		ref = f"S13-{frappe.generate_hash(length=8)}"
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "S-13 Legacy Manual Rule Denial"
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

	def test_S_13_tm2_v1_contamination_scan_clean(self) -> None:
		"""**P11-03** — TM2 package + desk assets contain no forbidden WORKS-LEGACY / v1 injection keys."""
		violations = run_tm2_v1_contamination_scan()
		self.assertFalse(
			violations,
			msg="P11-03 / S-13 contamination violations:\n" + format_violations(violations),
		)

	def test_S_13_manual_submission_rule_injection_save_denied_with_audit(self) -> None:
		"""**P11-01** — ``manual_submission_checklist_enabled`` in ``configuration_json`` → deny + audit."""
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

	def test_S_13_publish_without_std_template_denied_with_legacy_audit(self) -> None:
		"""**P11-01** / **P4-06** path — publish without STD → ``AUTH_LEGACY_PATH_DENIED`` + audit."""
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
