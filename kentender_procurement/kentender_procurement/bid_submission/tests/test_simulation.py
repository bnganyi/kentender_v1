# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 owner decision OD-C and plan D16: the Test Scanner
answers only on a test environment, and its verdicts name the simulation."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import file_integrity

from kentender_procurement.bid_submission.services import simulation
from kentender_procurement.bid_submission.test_services import scanner

EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


class TestSimulation(IntegrationTestCase):
	def switch(self, value):
		previous = frappe.conf.get(simulation.CONFIG_KEY)
		frappe.conf[simulation.CONFIG_KEY] = value
		self.addCleanup(frappe.conf.__setitem__, simulation.CONFIG_KEY, previous)

	def test_outside_a_test_environment_the_scanner_is_silent(self):
		self.switch(0)
		self.assertIsNone(scanner.scan(content=b"%PDF-1.4", filename="a.pdf"))
		self.assertEqual(file_integrity.scanner_result(b"%PDF-1.4", "a.pdf"), file_integrity.NOT_SCANNED)

	def test_on_a_test_environment_it_answers_and_says_it_is_a_simulation(self):
		self.switch(1)
		self.assertEqual(file_integrity.scanner_result(b"%PDF-1.4", "a.pdf"), "Clean — test scanner (simulation)")
		self.assertTrue(file_integrity.is_infected(file_integrity.scanner_result(EICAR, "eicar.pdf")))
