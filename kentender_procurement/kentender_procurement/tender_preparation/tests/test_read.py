# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §11.1 — the reads: verdict-first workspace, the Start
compatibility read, the editor (internal context visible to the officer,
read-only inherited rows), the approval task, the approved Tender, history
and preview (TPR-AC-002-style "reads create nothing", TPR-AC-044 visible
side, SMOKE-20)."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_preparation.services import read
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestWorkspace(TenderCase):
	def test_an_actor_without_a_responsibility_gets_the_forbidden_state_as_data(self):
		for user in (fx.OUTSIDER, fx.NOBODY):
			out = read.get_tender_preparation_workspace(user=user)
			self.assertEqual(out["outcome"], "FORBIDDEN", user)
			self.assertIn("Procurement Officer, Head of Procurement Function or Auditor", out["forbidden"]["text"])

	def test_the_officer_sees_the_eligible_handoff_and_no_approval_tasks(self):
		handoff = fx.authorised_handoff()
		out = read.get_tender_preparation_workspace(user=fx.OFFICER)
		self.assertEqual(out["outcome"], "OK")
		self.assertIn(handoff, [r["handoff"] for r in out["ready_to_prepare"]])
		self.assertTrue(out["ready_to_prepare"][0]["can_prepare"])
		self.assertFalse(out["show_approval_tasks"])
		self.assertEqual(out["tenders"], [])
		self.assertEqual(out["template"]["template_version"], "1.1")

	def test_the_head_sees_approval_tasks_and_cannot_prepare(self):
		sub = fx.submitted()
		out = read.get_tender_preparation_workspace(user=fx.HOPF)
		self.assertTrue(out["show_approval_tasks"])
		self.assertEqual([t["task"] for t in out["approval_tasks"]], [sub["task"]])
		self.assertFalse(out["can_prepare"])
		self.assertEqual(out["tenders"][0]["current_state"], "Submitted for approval")

	def test_a_consumed_handoff_leaves_the_ready_list(self):
		prep = fx.prepared()
		out = read.get_tender_preparation_workspace(user=fx.OFFICER)
		self.assertEqual(out["ready_to_prepare"], [])
		self.assertEqual(out["tenders"][0]["tender"], prep["tender"])

	def test_reads_create_nothing(self):
		fx.authorised_handoff()
		counts = lambda: (frappe.db.count("Prepared Tender"), frappe.db.count("Tender Preparation Version"), frappe.db.count("Tender Preparation Command Journal"))
		before = counts()
		read.get_tender_preparation_workspace(user=fx.OFFICER)
		read.get_tender_preparation_workspace(user=fx.HOPF)
		self.assertEqual(counts(), before)


class TestCompatibilityRead(TenderCase):
	def test_an_eligible_handoff_reads_compatible_with_counts_and_the_fixed_notice(self):
		handoff = fx.authorised_handoff()
		out = read.get_tender_compatibility(handoff=handoff, user=fx.OFFICER)
		self.assertEqual(out["outcome"], "OK")
		self.assertTrue(out["can_prepare"])
		self.assertEqual(out["counts"]["items"], 1)
		self.assertTrue(all(r["ok"] for r in out["compatibility"]))
		self.assertIn("fixed for this Tender", out["notice"])
		self.assertEqual(frappe.db.count("Prepared Tender"), 0)

	def test_a_consumed_handoff_reads_as_linked_with_a_view_route_when_authorised(self):
		prep = fx.prepared()
		handoff = frappe.get_doc("Prepared Tender", prep["tender"]).requisition_handoff
		out = read.get_tender_compatibility(handoff=handoff, user=fx.HOPF)
		self.assertEqual(out["outcome"], "HANDOFF_CONSUMED")
		self.assertEqual(out["tender"], prep["tender"])
		self.assertTrue(out["can_view"])

	def test_a_missing_handoff_reads_as_invalid_and_an_outsider_is_masked(self):
		self.assertEqual(read.get_tender_compatibility(handoff="RQH-NOPE", user=fx.OFFICER)["outcome"], "HANDOFF_INVALID")
		with self.assertRaises(frappe.DoesNotExistError):
			read.get_tender_compatibility(handoff="RQH-NOPE", user=fx.OUTSIDER)


class TestEditor(TenderCase):
	def test_the_editor_carries_inherited_rows_internal_context_and_permitted_actions(self):
		prep = fx.prepared()
		out = read.get_tender_editor(tender=prep["tender"], user=fx.OFFICER)
		self.assertEqual(out["outcome"], "OK")
		self.assertTrue(out["inherited"]["technical_requirements"])
		self.assertTrue(out["inherited"]["internal_context"]["internal_only"])
		self.assertIn("strategic_objective_path", out["inherited"]["internal_context"])
		self.assertTrue(out["permitted_actions"]["can_save"])
		self.assertFalse(out["tasks"]["1"]["complete"])
		self.assertTrue(out["tasks"]["2"]["complete"] and out["tasks"]["3"]["complete"])
		self.assertEqual(out["generated"]["tender_security_currency"], "KES")
		self.assertEqual(out["generated"]["price_schedule"]["rows"][0]["unit_price"], "Completed by Tenderer")
		self.assertIn("tender_title", out["controls"])

	def test_an_auditor_reads_but_cannot_act_and_an_outsider_is_masked(self):
		prep = fx.prepared()
		out = read.get_tender_editor(tender=prep["tender"], user=fx.AUDITOR)
		self.assertFalse(out["permitted_actions"]["can_save"])
		self.assertFalse(out["permitted_actions"]["can_request_upstream_correction"])
		with self.assertRaises(frappe.DoesNotExistError):
			read.get_tender_editor(tender=prep["tender"], user=fx.OUTSIDER)

	def test_a_returned_draft_carries_the_return_reason(self):
		from kentender_procurement.tender_preparation.services import lifecycle

		sub = fx.submitted()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		lifecycle.return_tender_for_correction(task=sub["task"], reason="Confirm whether manufacturer authorisation is necessary and update the evidence requirement.", expected_record_version=root.record_version, idempotency_key=fx.key())
		out = read.get_tender_editor(tender=sub["tender"], user=fx.OFFICER)
		self.assertIn("manufacturer authorisation", out["return_reason"])
		self.assertEqual(out["tender"]["version_number"], 2)


class TestApprovalTaskApprovedAndHistory(TenderCase):
	def test_the_approval_task_shows_renders_mappings_and_the_internal_context_but_renders_none_of_it(self):
		"""SMOKE-20 both halves, from the read side."""
		sub = fx.submitted()
		out = read.get_tender_approval_task(task=sub["task"], user=fx.HOPF)
		self.assertTrue(out["permitted_actions"]["can_approve"])
		self.assertTrue(out["inherited"]["internal_context"]["internal_only"])
		self.assertIn("technical", out["mappings"]["supplier_response_schema"])
		self.assertEqual(out["renders"]["problems"], [])
		for html in (out["renders"]["invitation_html"], out["renders"]["issued_tender_html"]):
			self.assertNotIn("Strategic Objective", html)
			self.assertNotIn("plan horizon", html.lower())
		officer_view = read.get_tender_approval_task(task=sub["task"], user=fx.OFFICER)
		self.assertFalse(officer_view["permitted_actions"]["can_approve"])
		both_view = read.get_tender_approval_task(task=sub["task"], user=fx.BOTH)
		self.assertTrue(both_view["permitted_actions"]["can_approve"])  # BOTH did not prepare this one

	def test_the_approved_tender_read_and_reopen_offer(self):
		app = fx.approved()
		out = read.get_approved_tender(tender=app["tender"], user=fx.HOPF)
		self.assertEqual(out["publication_handoff"]["status"], "Ready")
		self.assertTrue(out["permitted_actions"]["can_reopen"])
		self.assertTrue(out["renders"]["files"]["issued_tender_pdf_file"])
		self.assertFalse(read.get_approved_tender(tender=app["tender"], user=fx.AUDITOR)["permitted_actions"]["can_reopen"])
		history = read.get_tender_history(tender=app["tender"], user=fx.AUDITOR)
		self.assertEqual([v["version_status"] for v in history["versions"]], ["Approved"])
		self.assertEqual([d["decision"] for d in history["decisions"]], ["Approve for publication"])
		self.assertEqual(len(history["publication_handoffs"]), 1)

	def test_preview_renders_from_the_server_projection(self):
		prep = fx.prepared()
		fx.complete_draft(prep["tender"])
		out = read.get_tender_preview(tender=prep["tender"], output="invitation", user=fx.OFFICER)
		self.assertIn("INVITATION TO TENDER", out["html"])
		self.assertEqual(out["problems"], [])
		with self.assertRaises(Exception):
			read.get_tender_preview(tender=prep["tender"], output="other", user=fx.OFFICER)
