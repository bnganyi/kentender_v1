# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §5.10, §7.4 `GetSubmissionAvailability`, BDS07-AC-012/013
and plan D5/D6 (plan Phase 8, BDS8-801): one server-side gate, default off,
read from the site configuration only; the distinct answer for each failed
dependency in the stated order; simulated services answer only on a test
environment."""

from __future__ import annotations

import os
import re

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_submission.services import availability, gateways, simulation
from kentender_procurement.bid_submission.tests.support import submission_on

APPS = "/home/midasuser/frappe-bench/apps/kentender_v1"


class TestSubmissionAvailability(IntegrationTestCase):
	def setUp(self):
		submission_on(self)

	def code(self):
		return availability.get_submission_availability()["code"]

	def test_available_only_with_the_switch_on_and_every_service_healthy(self):
		self.assertEqual(availability.get_submission_availability(), {"available": True, "code": "", "message": ""})
		frappe.conf["production_bid_submission_enabled"] = 0
		self.assertEqual(self.code(), "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED")
		self.assertEqual(availability.get_submission_availability()["message"], "Electronic bid submission is not available yet. Your bid remains saved and has not been submitted.")

	def test_each_failed_dependency_has_its_own_answer_in_order(self):
		simulation.set_controls(trust_service_down=1, custody_service_down=1)
		self.assertEqual(self.code(), "BDS_SIGNATURE_UNAVAILABLE")
		simulation.set_controls(trust_service_down=0)
		self.assertEqual(self.code(), "BDS_SUBMISSION_SERVICE_UNAVAILABLE")
		simulation.set_controls(custody_service_down=0, time_service_down=1)
		self.assertEqual(self.code(), "BDS_SUBMISSION_SERVICE_UNAVAILABLE")
		simulation.set_controls(time_service_down=0, gate_closed=1, trust_service_down=1)
		self.assertEqual(self.code(), "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED")  # the gate comes first
		simulation.set_controls(gate_closed=0, trust_service_down=0)
		self.assertTrue(availability.get_submission_availability()["available"])

	def test_without_a_test_environment_no_service_answers(self):
		frappe.conf["kt_bds_simulation_environment"] = 0
		self.assertEqual((gateways.trust(), gateways.trusted_time(), gateways.custody()), (None, None, None))
		self.assertEqual(self.code(), "BDS_SIGNATURE_UNAVAILABLE")  # switch on, but no approved service configured
		with self.assertRaises(frappe.ValidationError):
			simulation.set_controls(gate_closed=1)

	def test_a_test_world_turns_the_switch_on_for_its_own_process_only(self):
		frappe.conf["production_bid_submission_enabled"] = 0
		with availability.enabled_for_test_world():
			self.assertTrue(availability.production_enabled())
		self.assertFalse(availability.production_enabled())
		frappe.conf["kt_bds_simulation_environment"] = 0
		with self.assertRaises(frappe.ValidationError):
			with availability.enabled_for_test_world():
				pass

	def test_nothing_but_the_availability_service_reads_the_switch(self):
		readers = []
		for app in ("kentender_core", "kentender_procurement", "kentender_suppliers"):
			for root, _dirs, files in os.walk(os.path.join(APPS, app)):
				if "/tests" in root or "node_modules" in root or "/dist" in root:
					continue
				for name in files:
					if name.endswith((".py", ".js", ".vue", ".json")):
						path = os.path.join(root, name)
						with open(path, encoding="utf-8", errors="ignore") as fh:
							if re.search(r"production_bid_submission_enabled", fh.read()):
								readers.append(os.path.relpath(path, APPS))
		self.assertEqual(readers, ["kentender_procurement/kentender_procurement/bid_submission/services/availability.py"])
