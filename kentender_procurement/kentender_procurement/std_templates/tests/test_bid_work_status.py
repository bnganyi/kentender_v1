# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.4.4 / plan D3–D4 — `bid_work_status`, the one read
Bid Submission uses to decide whether bid work on a Tender's bound release
may proceed. It never raises for a lifecycle state: it states the release's
lifecycle, site switch and integrity/renderer health, and Bid Submission
applies its own rule (Available On or Off permitted; Superseded/Withdrawn on
a published Tender fail closed until TPR v0.13; any integrity or renderer
failure fails closed)."""

from __future__ import annotations

import frappe

from kentender_procurement.std_templates.services import lifecycle, runtime
from kentender_procurement.std_templates.tests.test_binding import BindingCase

KEYS = {"release_id", "lifecycle", "site_switch", "integrity_ok", "renderer_ok", "problem"}


class TestBidWorkStatus(BindingCase):
	def test_an_available_release_reports_its_switch_and_health_either_way(self):
		release = self.install(switch="Off")
		status = runtime.bid_work_status(release)
		self.assertEqual(set(status), KEYS)
		self.assertEqual((status["lifecycle"], status["site_switch"], status["integrity_ok"], status["renderer_ok"], status["problem"]), ("Available", "Off", True, True, ""))

	def test_superseded_and_withdrawn_are_reported_not_raised(self):
		superseded = self.install()
		lifecycle.supersede(superseded, release_owner="test release owner")
		self.assertEqual(runtime.bid_work_status(superseded)["lifecycle"], "Superseded")
		withdrawn = self.install(template_release="9.7-test")
		lifecycle.withdraw(withdrawn, reason="Legal defect found in the reservation clause.", release_owner="test release owner")
		self.assertEqual(runtime.bid_work_status(withdrawn)["lifecycle"], "Withdrawn")

	def test_a_recorded_integrity_failure_is_reported_without_reverifying(self):
		release = self.install()
		frappe.db.set_value("Installed STD Release", release, {"integrity_status": "Failed", "integrity_problem": "Asset x no longer matches its installed digest."}, update_modified=False)
		status = runtime.bid_work_status(release)
		self.assertEqual((status["integrity_ok"], status["problem"]), (False, "Asset x no longer matches its installed digest."))

	def test_verify_rehashes_the_runtime_assets(self):
		release = self.install()
		doc = frappe.get_doc("Installed STD Release", release)
		row = next(a for a in doc.assets if a.relative_path in runtime.RUNTIME_PATHS)
		frappe.db.set_value("Installed STD Release Asset", row.name, "sha256_digest", "0" * 64, update_modified=False)
		self.assertTrue(runtime.bid_work_status(release)["integrity_ok"])  # the recorded state is still Verified
		verified = runtime.bid_work_status(release, verify=True)
		self.assertFalse(verified["integrity_ok"])
		self.assertIn(row.relative_path, verified["problem"])

	def test_an_unknown_release_is_not_available(self):
		status = runtime.bid_work_status("stdr-7e57-none")
		self.assertEqual((status["lifecycle"], status["integrity_ok"], status["renderer_ok"]), ("Unknown", False, False))
