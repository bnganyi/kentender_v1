# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The professional opinion (AWD-CHG-001 v0.4 §5.2, §5.3; AWD-AC-003, AC-005,
AC-006; tracker AWD4-302, AWD4-303)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import opinion, simulation, state
from kentender_procurement.award.services.errors import AwardError, InputError
from kentender_procurement.award.tests.support import AO, CASE, HOP, AwardCase

REASON = "The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the proposed award."


class TestOpinion(AwardCase):
	def test_sign_creates_decide_task(self):
		self.deliver()
		out = self.signed_opinion()
		self.assertTrue(out["ok"])
		self.assertEqual(out["task"], "Decide award")
		doc = self.case()
		self.assertEqual(doc.stage, "Decision")
		signed = state.signed_opinion(doc)
		self.assertEqual((signed.state, signed.conclusion, signed.version), ("Signed", "Recommend award", 1))
		self.assertTrue(signed.proof_reference.startswith("TATT-"))
		self.assertEqual(str(signed.signed_at), "2027-06-17 09:10:00")
		self.assertEqual(state.cycle(doc).opinion, signed.name)

	def test_only_the_head_of_procurement_signs(self):
		self.deliver()
		with self.assertRaises(AwardError) as ctx:
			self.run_as(AO, opinion.save, award=CASE, conclusion="Recommend award", reason=REASON, expected_version=self.version())
		self.assertEqual(ctx.exception.code, "AWD_AUTHORITY_REQUIRED")

	def test_a_stale_revision_changes_nothing(self):
		self.deliver()
		with self.assertRaises(AwardError) as ctx:
			self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason=REASON, expected_version=self.version() - 1)
		self.assertEqual(ctx.exception.code, "AWD_RECORD_CHANGED")
		self.assertEqual(state.opinions(self.case()), [])

	def test_signing_needs_a_conclusion_and_reason(self):
		self.deliver()
		self.run_as(HOP, opinion.save, award=CASE, conclusion="", reason="", expected_version=self.version())
		with self.assertRaises(InputError) as ctx:
			self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())
		self.assertEqual(set(ctx.exception.fields), {"conclusion", "reason"})

	def test_signing_unavailable_keeps_the_draft_and_the_same_attempt(self):
		self.deliver()
		self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason=REASON, expected_version=self.version())
		simulation.set_controls(signing_outcome="Unavailable")
		out = self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())
		self.assertFalse(out["ok"])
		self.assertEqual(out["code"], "AWD_SIGNATURE_UNAVAILABLE")
		self.assertEqual(out["message"], "Signing is unavailable. Your draft has been saved.")
		working = state.working_opinion(self.case())
		self.assertEqual((working.state, working.reason), ("Signing", REASON))
		self.assertEqual(self.case().stage, "Opinion")
		self.assertTrue(frappe.db.exists("Support Issue", {"module": "Award", "operation": "SignProfessionalOpinion", "status": "Open"}))
		simulation.set_controls(signing_outcome="")
		again = self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())
		self.assertTrue(again["ok"])
		self.assertEqual(state.signed_opinion(self.case()).signing_attempt, out["attempt"])
		self.assertFalse(frappe.db.exists("Support Issue", {"module": "Award", "operation": "SignProfessionalOpinion", "status": "Open"}))

	def test_incomplete_source_blocks_signing_but_not_the_draft(self):
		self.deliver(overrides={"missing_annex": True})
		self.run_as(HOP, opinion.save, award=CASE, conclusion="No current recommendation", reason="The report is incomplete.", expected_version=self.version())
		with self.assertRaises(AwardError) as ctx:
			self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())
		self.assertEqual(ctx.exception.code, "AWD_SOURCE_INCOMPLETE")

	def test_expired_report_supports_a_signed_factual_opinion(self):
		self.at("2027-10-11 09:00:00")
		self.deliver(overrides={"validity_end": "2027-10-10 11:00:00"})
		self.run_as(HOP, opinion.save, award=CASE, conclusion="No current recommendation", reason="Tender validity expired before an award could be notified.",
			expected_version=self.version())
		self.assertTrue(self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())["ok"])

	def test_a_recommendation_needs_a_supported_award(self):
		self.deliver("036")
		name = "AWD-AWT-2100-036"
		self.run_as(HOP, opinion.save, award=name, conclusion="Recommend award", reason="x", expected_version=self.version(name))
		with self.assertRaises(AwardError) as ctx:
			self.run_as(HOP, opinion.sign, award=name, expected_version=self.version(name))
		self.assertEqual(ctx.exception.code, "AWD_NO_SUPPORTED_AWARD")


class TestReturn(AwardCase):
	def test_return_waits_for_successor_and_keeps_versions(self):
		self.deliver()
		self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason=REASON, expected_version=self.version())
		out = self.run_as(HOP, opinion.return_report, award=CASE, reason="The service-location finding needs the committee's correction.",
			expected_version=self.version())
		self.assertTrue(out["ok"])
		doc = self.case()
		self.assertEqual(state.cycle(doc).awaiting_report, 1)
		self.assertEqual(state.report(doc.current_report).state, "Returned")
		self.assertEqual(state.opinions(doc)[0].state, "Out of date")
		with self.assertRaises(AwardError):
			self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason=REASON, expected_version=self.version())
		# the corrected report arrives: same case, same cycle, a fresh opinion is required
		self.at("2027-06-19 09:00:00")
		self.deliver(version=2, delivered_at="2027-06-19 09:00:00")
		doc = self.case()
		self.assertEqual((doc.current_cycle, state.cycle(doc).awaiting_report, state.current_report(doc).version_number), (1, 0, 2))
		self.assertEqual(frappe.db.count(state.REPORT, {"award_case": CASE}), 2)
		self.assertEqual(state.working_opinion(doc).state, "Out of date")
		with self.assertRaises(AwardError) as ctx:
			self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())
		self.assertEqual(ctx.exception.code, "AWD_RECORD_CHANGED")
		self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason=REASON, expected_version=self.version())
		self.assertTrue(self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())["ok"])
