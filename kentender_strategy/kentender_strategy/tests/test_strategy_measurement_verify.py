# Copyright (c) 2026, KenTender and contributors
"""STR-UI-10 Verify Measurement — transitions, SoD, Off-track CA / authorised exception."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import transition_measurement
from kentender_strategy.services.strategy_writes import get_measurement, save_measurement_draft


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_strategy_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
		"Performance Officer",
		"Performance Verifier",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


def _cleanup_measurement(name: str | None) -> None:
	if not name or not frappe.db.exists("Performance Measurement", name):
		return
	for ca in frappe.get_all(
		"Strategy Corrective Action",
		filters={"performance_measurement": name},
		pluck="name",
	):
		frappe.delete_doc("Strategy Corrective Action", ca, force=True, ignore_permissions=True)
	frappe.delete_doc("Performance Measurement", name, force=True, ignore_permissions=True)


class TestStrategyMeasurementVerify(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan_id = cls.seed["plan"]
		cls.target_id = cls.seed["target"]
		if cls.plan_id:
			status = frappe.db.get_value("Strategic Plan", cls.plan_id, "status")
			if status != "Active":
				frappe.db.set_value("Strategic Plan", cls.plan_id, "status", "Active")
		cls.officer = _ensure_user(
			"str.officer.verify@example.com", ["Performance Officer"], cls.pe
		)
		cls.verifier = _ensure_user(
			"str.verifier.verify@example.com", ["Performance Verifier"], cls.pe
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _submit_measurement(self, *, actual: float, period_start: str, period_end: str) -> str:
		frappe.set_user(self.officer)
		saved = save_measurement_draft(
			{
				"performance_target": self.target_id,
				"plan_version": self.plan_id,
				"measurement_period_start": period_start,
				"measurement_period_end": period_end,
				"measurement_date": period_end,
				"actual_numeric": actual,
				"evidence_source": "Verify test evidence",
				"evidence_reference": "VERIFY-TEST-REF",
				"commentary": "Submitted for verify tests",
			}
		)
		mid = saved["id"]
		self.addCleanup(lambda: _cleanup_measurement(mid))
		tr = transition_measurement(mid, "Submit")
		self.assertEqual(tr["workflow_status"], "Submitted")
		return mid

	def test_get_measurement_verify_purpose_prefers_submitted(self):
		mid = self._submit_measurement(
			actual=99.85, period_start="2026-09-01", period_end="2026-09-30"
		)
		frappe.set_user(self.verifier)
		m = get_measurement(
			target_code=TARGET_CODE, plan_code=STRATEGY_PLAN_CODE, purpose="verify"
		)
		self.assertEqual(m.get("id"), mid)
		self.assertEqual(m.get("workflow_status"), "Submitted")
		self.assertFalse(m.get("is_new"))
		self.assertIn("measurement_date", m)
		self.assertIn("submitted_at", m)
		self.assertIn("verified_at", m)

	def test_verify_submitted_optional_comment(self):
		mid = self._submit_measurement(
			actual=99.96, period_start="2026-10-01", period_end="2026-10-31"
		)
		frappe.set_user(self.verifier)
		tr = transition_measurement(mid, "Verify", reason=None)
		self.assertEqual(tr["workflow_status"], "Verified")
		doc = frappe.get_doc("Performance Measurement", mid)
		self.assertEqual(doc.verified_by, self.verifier)
		self.assertTrue(doc.verified_at)

	def test_return_and_reject_require_reason(self):
		mid_r = self._submit_measurement(
			actual=99.9, period_start="2026-11-01", period_end="2026-11-15"
		)
		mid_j = self._submit_measurement(
			actual=99.9, period_start="2026-11-16", period_end="2026-11-30"
		)
		frappe.set_user(self.verifier)
		with self.assertRaises(frappe.ValidationError):
			transition_measurement(mid_r, "Return", reason=None)
		with self.assertRaises(frappe.ValidationError):
			transition_measurement(mid_j, "Reject", reason="")
		tr = transition_measurement(mid_r, "Return", reason="Needs clearer evidence")
		self.assertEqual(tr["workflow_status"], "Returned")
		self.assertEqual(
			frappe.db.get_value("Performance Measurement", mid_r, "verification_comment"),
			"Needs clearer evidence",
		)
		tr2 = transition_measurement(mid_j, "Reject", reason="Not credible")
		self.assertEqual(tr2["workflow_status"], "Rejected")

	def test_submitter_cannot_verify_own_measurement(self):
		mid = self._submit_measurement(
			actual=99.9, period_start="2026-12-01", period_end="2026-12-15"
		)
		# Officer also holds Performance Verifier for the negative path.
		_ensure_user(self.officer, ["Performance Officer", "Performance Verifier"], self.pe)
		frappe.set_user(self.officer)
		with self.assertRaises(frappe.PermissionError):
			transition_measurement(mid, "Verify")
		# Restore officer-only roles for later tests.
		_ensure_user(self.officer, ["Performance Officer"], self.pe)

	def test_off_track_verify_creates_corrective_action(self):
		# Target 99.9 / tol 0.1 → below 99.8 is Off track.
		mid = self._submit_measurement(
			actual=99.5, period_start="2027-01-01", period_end="2027-01-31"
		)
		frappe.set_user(self.verifier)
		tr = transition_measurement(mid, "Verify")
		self.assertEqual(tr["workflow_status"], "Verified")
		self.assertEqual(tr["result_status"], "Off track")
		ca = frappe.db.exists(
			"Strategy Corrective Action",
			{"performance_measurement": mid, "status": ["not in", ["Cancelled"]]},
		)
		self.assertTrue(ca)

	def test_off_track_verify_authorised_exception_skips_ca(self):
		mid = self._submit_measurement(
			actual=99.4, period_start="2027-02-01", period_end="2027-02-28"
		)
		frappe.set_user(self.verifier)
		tr = transition_measurement(
			mid,
			"Verify",
			reason="Accepted seasonal outage",
			authorised_exception=True,
			exception_reason="Authorised seasonal maintenance window",
		)
		self.assertEqual(tr["workflow_status"], "Verified")
		self.assertEqual(tr["result_status"], "Off track")
		doc = frappe.get_doc("Performance Measurement", mid)
		self.assertTrue(doc.authorised_exception)
		self.assertEqual(doc.exception_reason, "Authorised seasonal maintenance window")
		ca = frappe.db.exists(
			"Strategy Corrective Action",
			{"performance_measurement": mid, "status": ["not in", ["Cancelled"]]},
		)
		self.assertFalse(ca)
