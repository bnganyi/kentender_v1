# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who sees what (AWD-CHG-001 v0.4 §6; AWD-AC-024; tracker AWD4-1001, AWD4-1003).
Internal, supplier, auditor, public and technical readers across record,
workspace, notice, task titles, support issues and API refusals; nothing
follows merely from knowing an identifier."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.award import api, portal
from kentender_procurement.award.services import decision, reads, simulation, state, supplier, tasks
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.tests.support import AO, CASE, DANIEL, DAVID, HOP, MARY, NAOMI, AwardCase

OUTSIDER = "brian.wafula@moh.example.test"
NAME37 = "AWD-AWT-2100-037"
BUSINESS = ("Afya", "Jirani", "KES", "46,400,000", "45,900,000", "46400000", "lowest evaluated")


class TestLeakage(AwardCase):
	def test_technical_readers_see_operations_only(self):
		simulation.set_controls(email_service_down=1)
		self.deliver()
		self.awarded()
		view = json.dumps(reads.record(award=CASE, user=DANIEL), default=str)
		for word in BUSINESS:
			self.assertNotIn(word, view)
		self.assertIn("Restore notice delivery", view)
		for name in frappe.get_all("Support Issue", filters={"module": "Award", "reference_name": CASE}, pluck="name"):
			issue = frappe.get_doc("Support Issue", name)
			for word in BUSINESS:
				self.assertNotIn(word, issue.subject + (issue.safe_detail or ""))

	def test_the_auditor_reads_without_any_action(self):
		self.deliver()
		out = reads.record(award=CASE, user=NAOMI)
		self.assertFalse(any(out["actions"].values()))
		from kentender_procurement.award.services import opinion

		with self.assertRaises(AwardError) as ctx:
			self.run_as(NAOMI, opinion.save, award=CASE, conclusion="Recommend award", reason="x", expected_version=self.version())
		self.assertEqual(ctx.exception.code, "AWD_AUTHORITY_REQUIRED")

	def test_outsiders_suppliers_and_guests_get_not_found(self):
		self.deliver()
		for user in (OUTSIDER, MARY, DAVID, "Guest"):
			with self.assertRaises(frappe.DoesNotExistError):
				reads.record(award=CASE, user=user)
		self.assertTrue(reads.workspace(user=OUTSIDER)["forbidden"])
		frappe.set_user(MARY)
		try:
			with self.assertRaises(frappe.DoesNotExistError):
				api.get_award(CASE)
		finally:
			frappe.set_user("Administrator")

	def test_a_supplier_sees_only_their_own_letter(self):
		self.deliver("037")
		self.awarded(NAME37)
		batch = state.current_batch(self.case(NAME37))
		by = {n.organisation_name: n for n in state.notices(batch)}
		mine = supplier.notice_view(notice=by["Afya Digital Supplies Limited"].name, user=MARY)
		text = json.dumps(mine, default=str)
		self.assertNotIn(by["Jirani Office Supplies Limited"].name, text)
		for internal in ("Grace Wambui", "Professional opinion", "position", "Charles Mutiso", "I accept the recommendation"):
			self.assertNotIn(internal, text)
		with self.assertRaises(frappe.DoesNotExistError):
			supplier.notice_view(notice=by["Jirani Office Supplies Limited"].name, user=MARY)
		with self.assertRaises(frappe.DoesNotExistError):
			supplier.notice_view(notice=by["Afya Digital Supplies Limited"].name, user=HOP)

	def test_the_portal_asks_guests_to_sign_in(self):
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.assertEqual(portal.resolve(path=f"/supplier/awards/{notice.name}", user="Guest")["verdict"], "SIGN_IN")
		self.assertEqual(portal.resolve(path=f"/supplier/awards/{notice.name}", user=OUTSIDER)["verdict"], "NOT_FOUND")
		self.assertEqual(portal.resolve(path=f"/supplier/awards/{notice.name}", user=MARY)["verdict"], "OK")

	def test_task_titles_carry_no_business_facts(self):
		self.deliver()
		self.signed_opinion()
		for user in (HOP, AO):
			for row in tasks.my_work_rows(user)["assigned"]:
				for word in BUSINESS:
					self.assertNotIn(word, row["title"])

	def test_refusals_disclose_no_other_facts(self):
		self.deliver()
		self.signed_opinion()
		frappe.set_user(HOP)
		try:
			out = api.record_decision(CASE, outcome="Award", reason="x", expected_version=self.version(), idempotency_key=self.key())
		finally:
			frappe.set_user("Administrator")
		self.assertEqual((out["ok"], out["code"]), (False, "AWD_AUTHORITY_REQUIRED"))
		self.assertNotIn("Afya", json.dumps(out))
		self.assertEqual(state.committed_decision(self.case()), None)
