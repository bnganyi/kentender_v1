# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WG-01 Readiness Check API contract tests."""

from __future__ import annotations

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.constants import (
	STATUS_READY_FOR_REVIEW,
	STATUS_RETURNED_FOR_CORRECTION,
	STATUS_UNDER_REVIEW,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.readiness import (
	get_readiness_report,
	run_readiness_check,
	submit_for_review,
)
from kentender_procurement.tender_configurations.services.review_workspace import (
	return_for_correction,
)


class TestConfigurationReadinessApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape_before_run(self):
		out = get_readiness_report(self.cfg_id)
		for key in (
			"configuration_id",
			"overall_result",
			"findings",
			"checklist",
			"can_submit_for_review",
			"review_corrections",
			"open_correction_count",
			"context",
		):
			self.assertIn(key, out)
		self.assertFalse(out["has_run"])
		self.assertEqual(out["open_correction_count"], 0)

	def test_run_check_on_incomplete_has_blockers(self):
		out = run_readiness_check(self.cfg_id)
		self.assertTrue(out["has_run"])
		self.assertGreater(out["blocker_count"], 0)
		self.assertFalse(out["can_submit_for_review"])
		self.assertEqual(len(out["checklist"]), 9)

	def test_submit_blocked_when_blockers(self):
		run_readiness_check(self.cfg_id)
		with self.assertRaises(Exception):
			submit_for_review(self.cfg_id, {})

	def test_submit_when_clear(self):
		# Force clear readiness blob and Ready for Review path by zeroing blockers via mock save
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		# Mark steps complete in steps_state and clear CFG JSON enough that probes pass is hard;
		# instead inject a clear readiness report then submit.
		blob = {
			"findings": [],
			"checklist": [
				{
					"step_id": f"CFG-0{i}",
					"area": f"Area {i}",
					"check_result": "Complete",
					"action_label": "Review",
					"owner_route": "",
				}
				for i in range(1, 10)
			],
			"blocker_count": 0,
			"warning_count": 0,
			"overall_result": "Ready for Review",
			"last_checked_at": "2026-07-19 10:00:00",
			"last_checked_by": "Administrator",
		}
		doc.readiness_report = json.dumps(blob)
		doc.blocker_count = 0
		doc.warning_count = 0
		doc.status = STATUS_READY_FOR_REVIEW
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		out = submit_for_review(self.cfg_id, {"acknowledge_warnings": 1})
		self.assertTrue(out.get("submitted"))
		doc.reload()
		self.assertEqual(doc.status, STATUS_UNDER_REVIEW)

	def test_rerun_keeps_returned_while_open_corrections(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
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

		return_for_correction(
			self.cfg_id,
			{"affected_section": "CFG-03", "correction_required": "Fix returned item"},
		)
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_RETURNED_FOR_CORRECTION)

		# Force zero blockers on disk so re-run would historically auto-promote.
		doc.blocker_count = 0
		doc.readiness_report = json.dumps(
			{
				"findings": [],
				"checklist": [
					{
						"step_id": f"CFG-0{i}",
						"area": f"Area {i}",
						"check_result": "Complete",
						"action_label": "Review",
						"owner_route": "",
					}
					for i in range(1, 10)
				],
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

		# Patch run path: if real probes still find blockers, status becomes Needs Attention —
		# assert open corrections still block Ready promotion when blockers clear.
		from unittest.mock import patch

		with patch(
			"kentender_procurement.tender_configurations.services.readiness._build_findings_and_checklist",
			return_value=([], [], 0, 0),
		):
			out = run_readiness_check(self.cfg_id)
		self.assertEqual(out["open_correction_count"], 1)
		self.assertFalse(out["can_submit_for_review"])
		doc.reload()
		self.assertEqual(doc.status, STATUS_RETURNED_FOR_CORRECTION)
