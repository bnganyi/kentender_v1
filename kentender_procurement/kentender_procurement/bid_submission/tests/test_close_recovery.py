# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The close at the deadline without a running scheduler (follow-up
FU-V08-44; owner, 27 Sep 2026: "make this more robust"). A Tender whose
deadline passed more than 15 minutes ago without a Bid Submission close is
overdue: the Technical Operator sees it in the submission-service status read
(no scheduler needed) and, whenever the sweep runs, as an incident. The
recovery command ends the Tenders submission period if it is still open,
then closes Bid Submission and issues the Bid Opening hand-off — once; a
second run changes nothing. Only a technical operator may run it."""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import get_datetime

from kentender_procurement.bid_submission.services import close, handoffs, technical_read
from kentender_procurement.bid_submission.tests.support import MARY
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase


class TestOverdueClose(ChangeCase):
	def at_offset(self, minutes: int) -> None:
		self.at(str(get_datetime(self.deadline()) + timedelta(minutes=minutes)))

	def test_an_overdue_close_is_visible_and_recovered_once_by_the_operator(self):
		self.submitted()
		self.at_offset(10)  # within the grace period: the scheduler may still be on its way
		self.assertEqual(close.overdue_closes(), [])
		self.at_offset(20)
		overdue = close.overdue_closes()
		self.assertEqual([(o["tender_reference"], o["tenders_period_ended"]) for o in overdue], [(self.reference, False)])
		status = technical_read.get_submission_service_status(user="Administrator")
		self.assertEqual([o["tender_reference"] for o in status["overdue_closes"]], [self.reference])
		handoffs.sync_incidents()
		incident = frappe.db.get_value("Bid Submission Incident", {"incident_key": f"close-overdue:{self.name}", "status": "Open"}, ["kind", "holder_role", "reference"], as_dict=True)
		self.assertEqual((incident.kind, incident.holder_role, incident.reference), ("Submission close", "Technical Operator", self.reference))
		# a supplier cannot run the recovery
		with self.assertRaises(frappe.PermissionError):
			close.recover_overdue_close(tender_reference=self.reference, user=MARY)
		done = close.recover_overdue_close(tender_reference=self.reference, user="Administrator")
		self.assertEqual((done["ok"], done["action"]), (True, "closed"))
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Submission period ended")
		sealed = frappe.db.get_value("Bid Submission Close", {"tender": self.name}, ["name", "bid_opening_handoff"], as_dict=True)
		self.assertTrue(sealed and sealed.bid_opening_handoff)
		self.assertEqual(close.overdue_closes(), [])
		handoffs.sync_incidents()
		self.assertEqual(frappe.db.get_value("Bid Submission Incident", {"incident_key": f"close-overdue:{self.name}"}, "status"), "Resolved")
		again = close.recover_overdue_close(tender_reference=self.reference, user="Administrator")
		self.assertEqual((again["ok"], again["action"]), (True, "already_closed"))
		self.assertEqual(frappe.db.count("Bid Opening Handoff", {"tender": self.name}), 1)
