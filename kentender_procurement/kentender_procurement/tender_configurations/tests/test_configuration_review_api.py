# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WG-02 Review Workspace API contract tests."""

from __future__ import annotations

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
	STATUS_READY_FOR_REVIEW,
	STATUS_RETURNED_FOR_CORRECTION,
	STATUS_UNDER_REVIEW,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.readiness import (
	get_readiness_report,
	submit_for_review,
)
from kentender_procurement.tender_configurations.services.review_workspace import (
	REVIEWER_CHECKLIST,
	SEV_CORRECTION,
	approve_for_preview,
	get_review_workspace,
	resolve_review_finding,
	return_for_correction,
	save_review_workspace,
)


def _add_open_correction(cfg_id: str, section: str = "CFG-03", reason: str = "Fix acceptance expectations"):
	ws = get_review_workspace(cfg_id)
	findings = list(ws.get("findings") or [])
	findings.append(
		{
			"finding": reason[:120],
			"section": section,
			"severity": SEV_CORRECTION,
			"required_action": reason,
			"status": "Open",
		}
	)
	return save_review_workspace(cfg_id, {"checklist": ws.get("checklist") or [], "findings": findings})


def _put_under_review(cfg_id: str):
	doc = frappe.get_doc("Tender Configuration", cfg_id)
	doc.status = STATUS_UNDER_REVIEW
	doc.blocker_count = 0
	doc.readiness_report = json.dumps(
		{
			"findings": [],
			"checklist": [],
			"blocker_count": 0,
			"warning_count": 0,
			"overall_result": "Ready for Review",
			"last_checked_at": "2026-07-19 10:00:00",
			"submitted_at": "2026-07-19 10:05:00",
			"submitted_by": "Administrator",
		}
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()


class TestConfigurationReviewApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		_put_under_review(self.cfg_id)

	def test_get_shape_and_checklist(self):
		out = get_review_workspace(self.cfg_id)
		self.assertEqual(len(out["checklist"]), 10)
		self.assertEqual(out["checklist"][0]["label"], REVIEWER_CHECKLIST[0])
		self.assertFalse(out["can_approve"])

	def test_approve_gated_on_checklist(self):
		with self.assertRaises(Exception):
			approve_for_preview(self.cfg_id, {"confirm_preview_only": 1})

	def test_approve_when_checklist_complete(self):
		ws = get_review_workspace(self.cfg_id)
		for item in ws["checklist"]:
			item["checked"] = 1
		save_review_workspace(self.cfg_id, {"checklist": ws["checklist"]})
		out = approve_for_preview(self.cfg_id, {"confirm_preview_only": 1})
		self.assertTrue(out.get("approved"))
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_APPROVED_FOR_PREVIEW)

	def test_return_requires_open_correction_findings(self):
		with self.assertRaises(Exception) as ctx:
			return_for_correction(self.cfg_id, {"confirm_return": 1})
		exc = ctx.exception
		self.assertTrue(
			getattr(exc, "title", None) == "RETURN_FINDINGS_REQUIRED"
			or "Correction Required finding" in str(exc),
			msg=str(exc),
		)
		# Compat: payload with section+reason still creates the finding then returns.
		out = return_for_correction(
			self.cfg_id,
			{"affected_section": "CFG-03", "correction_required": "Fix acceptance expectations"},
		)
		self.assertTrue(out.get("returned"))
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_RETURNED_FOR_CORRECTION)

	def test_return_confirm_uses_existing_findings(self):
		saved = _add_open_correction(self.cfg_id)
		self.assertTrue(saved.get("return_enabled"))
		self.assertGreaterEqual(int(saved.get("open_correction_count") or 0), 1)
		before_n = len(saved.get("findings") or [])
		out = return_for_correction(self.cfg_id, {"confirm_return": 1})
		self.assertTrue(out.get("returned"))
		self.assertEqual(len(out.get("findings") or []), before_n)
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_RETURNED_FOR_CORRECTION)

	def test_get_starts_review_from_ready_for_review(self):
		"""Opening WG-02 while Ready for Review auto-starts Under Review; Return needs findings."""
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		doc.status = STATUS_READY_FOR_REVIEW
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		out = get_review_workspace(self.cfg_id)
		self.assertFalse(out["return_enabled"])
		self.assertTrue(out["clarify_enabled"])
		self.assertIn("under review", (out.get("review_status_label") or "").lower())
		doc.reload()
		self.assertEqual(doc.status, STATUS_UNDER_REVIEW)
		saved = _add_open_correction(self.cfg_id)
		self.assertTrue(saved["return_enabled"])

	def test_return_assigns_stable_finding_id(self):
		_add_open_correction(self.cfg_id, reason="Clarify RFP scope")
		return_for_correction(self.cfg_id, {"confirm_return": 1})
		report = get_readiness_report(self.cfg_id)
		self.assertGreaterEqual(report["open_correction_count"], 1)
		finding = report["review_corrections"][0]
		self.assertTrue(str(finding.get("id") or "").startswith("FIN-"))
		self.assertEqual(finding.get("status"), "Open")

	def test_submit_blocked_while_open_corrections(self):
		_add_open_correction(self.cfg_id)
		return_for_correction(self.cfg_id, {"confirm_return": 1})
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		doc.blocker_count = 0
		doc.readiness_report = json.dumps(
			{
				"findings": [],
				"checklist": [],
				"blocker_count": 0,
				"warning_count": 0,
				"overall_result": "Ready for Review",
				"last_checked_at": "2026-07-19 10:00:00",
				"last_checked_by": "Administrator",
			}
		)
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		report = get_readiness_report(self.cfg_id)
		self.assertFalse(report["can_submit_for_review"])
		self.assertGreater(report["open_correction_count"], 0)
		with self.assertRaises(Exception) as ctx:
			submit_for_review(self.cfg_id, {"acknowledge_warnings": 1})
		exc = ctx.exception
		self.assertTrue(
			getattr(exc, "title", None) == "REVIEW_CORRECTIONS_OPEN"
			or "Mark all reviewer corrections as fixed" in str(exc),
			msg=str(exc),
		)

	def test_resolve_all_corrections_allows_submit(self):
		_add_open_correction(self.cfg_id)
		return_for_correction(self.cfg_id, {"confirm_return": 1})
		report = get_readiness_report(self.cfg_id)
		fid = report["review_corrections"][0]["id"]
		resolved = resolve_review_finding(self.cfg_id, fid)
		self.assertEqual(resolved["open_correction_count"], 0)

		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		doc.blocker_count = 0
		doc.readiness_report = json.dumps(
			{
				"findings": [],
				"checklist": [],
				"blocker_count": 0,
				"warning_count": 0,
				"overall_result": "Ready for Review",
				"last_checked_at": "2026-07-19 10:00:00",
				"last_checked_by": "Administrator",
			}
		)
		doc.status = "Ready for Review"
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		out = submit_for_review(self.cfg_id, {"acknowledge_warnings": 1})
		self.assertTrue(out.get("submitted"))
		doc.reload()
		self.assertEqual(doc.status, STATUS_UNDER_REVIEW)
