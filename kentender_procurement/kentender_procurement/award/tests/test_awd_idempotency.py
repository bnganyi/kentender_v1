# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Retries, stale revisions and out-of-order events (AWD-CHG-001 v0.4 §7, §12;
AWD-AC-025; tracker AWD4-1003): no duplicate decision, notice, response,
work item or consumer case; a stale write changes nothing."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import corrections, decision, eligibility, intake, opinion, restrictions, state, supplier
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, CASE, HOP, MARY, AwardCase
from kentender_procurement.award.tests.test_awd_corrections import CORRECTION


class TestIdempotency(AwardCase):
	def test_repeated_commands_return_their_first_result(self):
		self.deliver()
		self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason="ok", expected_version=self.version())
		key, v = self.key("sign"), self.version()
		first = self.run_as(HOP, opinion.sign, award=CASE, expected_version=v, idempotency_key=key)
		self.assertEqual(self.run_as(HOP, opinion.sign, award=CASE, expected_version=v, idempotency_key=key), first)
		self.assertEqual(len([o for o in state.opinions(self.case()) if o.state == "Signed"]), 1)
		self.at("2027-06-17 10:00:00")
		self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="ok", expected_version=self.version())
		notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 09:00:00")
		key = self.key("respond")
		a = self.run_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=1, idempotency_key=key)
		self.assertEqual(self.run_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=1, idempotency_key=key), a)
		self.assertEqual(frappe.db.count(state.RESPONSE, {"notice": notice.name}), 1)
		with self.assertRaises(AwardError):
			self.run_as(MARY, supplier.respond, notice=notice.name, response="Decline", reason="x", notice_version=1)
		key = self.key("restriction")
		args = dict(award=CASE, basis="Reported challenge", source="Letter", received_at="2027-06-18 10:00:00", reason="x", idempotency_key=key)
		self.run_as(HOP, restrictions.record_external, **args)
		self.run_as(HOP, restrictions.record_external, **args)
		self.assertEqual(frappe.db.count(state.ISSUE, {"award_case": CASE, "issue_type": "Review/order"}), 1)

	def test_a_stale_revision_changes_nothing(self):
		self.deliver()
		self.signed_opinion()
		with self.assertRaises(AwardError) as ctx:
			self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="ok", expected_version=self.version() - 1)
		self.assertEqual(ctx.exception.code, "AWD_RECORD_CHANGED")
		self.assertEqual(frappe.db.count(state.DECISION, {"award_case": CASE}), 0)
		self.assertEqual(frappe.db.count(state.BATCH, {"award_case": CASE}), 0)

	def test_out_of_order_and_repeated_events(self):
		self.deliver()
		self.awarded()
		tender = self.case().tender
		syn.add_correction(tender, CORRECTION)
		corrections.pull_case(CASE)
		corrections.pull_case(CASE)
		self.assertEqual(frappe.db.count(state.ISSUE, {"award_case": CASE, "issue_type": "Source correction"}), 1)
		intake.receive(delivery=f"SYN-DLV:{self.reference}:1", source_kind="Synthetic")
		self.assertEqual(frappe.db.count(state.REPORT, {"award_case": CASE}), 1)

	def test_package_delivery_is_one_receipt(self):
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=1)
		self.at("2027-07-02 09:00:00")
		eligibility.refresh_case(CASE)
		eligibility.refresh_case(CASE)
		self.assertEqual(frappe.db.count("Award Test Contracting Inbox", {"award_case": CASE, "kind": "Package"}), 1)
		self.assertEqual(frappe.db.count(state.PACKAGE, {"award_case": CASE}), 1)
