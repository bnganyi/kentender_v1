# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Authorised Signatory panel says who can change the signatory and what a
missing certificate means (owner report, 2 Oct 2026: the preparer, David, could
not change the signatory or fix the certificate and the page did not say why).
Pure logic: no database."""

from __future__ import annotations

from unittest import TestCase

from kentender_procurement.bid_submission.services import company_view


class TestSignatoryNotes(TestCase):
	def notes(self, **kw):
		base = {"name": "Mary Wanjiku", "organisation": "Afya Digital Supplies (Test) Limited", "viewer_is_signatory": False, "joint": False, "certificate_ready": True}
		return company_view.signatory_notes(**{**base, **kw})

	def test_a_preparer_is_told_who_can_change_the_signatory_and_where(self):
		out = self.notes()
		self.assertEqual(out["change_note"], "Only an Authorised Signatory of Afya Digital Supplies (Test) Limited can change who signs, in the Account under People. Ask Mary Wanjiku.")
		self.assertEqual(out["change_href"], "")

	def test_a_signatory_is_pointed_at_the_account(self):
		out = self.notes(viewer_is_signatory=True)
		self.assertEqual((out["change_note"], out["change_href"]), ("You can change who signs in your Account, under People.", "/account"))

	def test_a_joint_venture_signatory_was_named_when_the_bid_started(self):
		out = self.notes(joint=True)
		self.assertEqual(out["change_note"], "The Authorised Signatory was named when this joint-venture bid was started.")
		self.assertEqual(out["change_href"], "")

	def test_a_missing_certificate_says_what_it_means_and_a_ready_one_says_nothing(self):
		self.assertEqual(self.notes(certificate_ready=False)["certificate_note"], "Mary Wanjiku needs a digital certificate from the signing service before this bid can be submitted.")
		self.assertEqual(self.notes(certificate_ready=True)["certificate_note"], "")
