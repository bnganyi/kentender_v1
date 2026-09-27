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

	def test_the_shared_test_instant_is_set_and_cleared_through_kentender_core(self):
		from kentender_core.services import test_clock

		self.switch(1)
		self.addCleanup(simulation.reset_controls)
		self.assertTrue(test_clock.set_instant("2027-05-19 10:00:00"))
		self.assertEqual(str(test_clock.current_instant()), "2027-05-19 10:00:00")
		self.assertTrue(test_clock.set_instant(None))
		self.assertIsNone(test_clock.current_instant())

	def test_outside_a_test_environment_nothing_takes_the_instant(self):
		from kentender_core.services import test_clock

		self.switch(0)
		self.assertFalse(test_clock.set_instant("2027-05-19 10:00:00"))
		self.assertIsNone(test_clock.current_instant())


class TestMailbox(IntegrationTestCase):
	"""The Test Mailbox: supplier messages on a test environment land where a
	browser world can open their links; elsewhere it declines every message."""

	TO = "pw.mailbox.test@mailbox-test.example"

	def switch(self, value):
		previous = frappe.conf.get(simulation.CONFIG_KEY)
		frappe.conf[simulation.CONFIG_KEY] = value
		self.addCleanup(frappe.conf.__setitem__, simulation.CONFIG_KEY, previous)

	def setUp(self):
		from kentender_procurement.bid_submission.test_services import mailbox

		self.mailbox = mailbox
		self.addCleanup(mailbox.clear, self.TO)

	def test_on_a_test_environment_a_message_is_kept_for_its_recipient(self):
		self.switch(1)
		answer = self.mailbox.deliver({"to": self.TO, "subject": "Verify", "body": "Open https://x/account/verify?token=abc", "link": "https://x/account/verify?token=abc"})
		self.assertEqual(answer, {"result": "Delivered to the test mailbox (simulation)"})
		self.assertEqual(self.mailbox.latest(self.TO)["link"], "https://x/account/verify?token=abc")
		self.mailbox.clear(self.TO)
		self.assertIsNone(self.mailbox.latest(self.TO))

	def test_outside_a_test_environment_it_declines(self):
		self.switch(0)
		self.assertIsNone(self.mailbox.deliver({"to": self.TO, "subject": "Verify", "body": "…"}))
		self.assertIsNone(self.mailbox.latest(self.TO))

	def test_it_carries_the_supplier_account_verification_message(self):
		self.switch(1)
		from kentender_core.services import test_clock  # noqa: F401 — the hook is declared by procurement

		self.assertIn("kentender_procurement.bid_submission.test_services.mailbox.deliver", frappe.get_hooks("kt_supplier_account_message_transports"))
		self.assertIn("kentender_procurement.bid_submission.test_services.mailbox.deliver", frappe.get_hooks("kt_bds_supplier_message_transports"))
