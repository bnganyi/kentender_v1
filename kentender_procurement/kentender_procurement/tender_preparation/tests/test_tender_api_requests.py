# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §11 — request-shaped endpoint tests: the framework's
own `execute_cmd` over a populated `form_dict`, an AST guard against
`**kwargs` and bare `values`, every role including Administrator and
System Manager against the business gates (TPR-AC-030/040, SMOKE-19), and
the technical acknowledgment endpoint reserved to System Manager."""

from __future__ import annotations

import ast
import inspect
import json

import frappe
from frappe.handler import execute_cmd

from kentender_procurement.tender_preparation import api
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase

API = "kentender_procurement.tender_preparation.api"


class RequestShapedCase(TenderCase):
	def setUp(self):
		super().setUp()
		self.addCleanup(setattr, frappe.local, "form_dict", frappe._dict())

	def call(self, method: str, **args):
		frappe.local.form_dict = frappe._dict(cmd=f"{API}.{method}", csrf_token="irrelevant-but-present-on-every-post", **args)
		had_request = hasattr(frappe.local, "request")
		if not had_request:
			frappe.local.request = frappe._dict(method="POST", path=f"/api/method/{API}.{method}", headers={})
			self.addCleanup(delattr, frappe.local, "request")
		return execute_cmd(f"{API}.{method}")


class TestJourneyOverHttpShape(RequestShapedCase):
	def test_prepare_save_readiness_submit_return_resubmit_approve(self):
		handoff = fx.authorised_handoff()
		frappe.set_user(fx.OFFICER)
		ws = self.call("get_tender_preparation_workspace")
		self.assertEqual(ws["outcome"], "OK")
		compat = self.call("get_tender_compatibility", handoff=handoff)
		self.assertEqual(compat["outcome"], "OK")
		prepared = self.call("prepare_tender", handoff=handoff, idempotency_key=fx.key())
		tender = prepared["tender"]
		saved = self.call("save_tender_draft", tender=tender, draft_values=json.dumps({**fx.TASK1, **fx.TASK4, **fx.TASK5}), expected_record_version=str(prepared["record_version"]), idempotency_key=fx.key())
		self.assertTrue(saved["ok"], saved)
		editor = self.call("get_tender_editor", tender=tender)
		self.assertTrue(editor["tasks"]["1"]["complete"])
		ready = self.call("run_tender_readiness", tender=tender, expected_record_version=str(saved["record_version"]), idempotency_key=fx.key())
		self.assertTrue(ready["ready"], ready["findings"])
		preview = self.call("get_tender_preview", tender=tender, output="issued_tender")
		self.assertIn("Section V - Schedule of Requirements", preview["html"])
		submitted = self.call("submit_tender_for_approval", tender=tender, expected_record_version=str(ready["record_version"]), idempotency_key=fx.key())
		frappe.set_user(fx.HOPF)
		task = self.call("get_tender_approval_task", task=submitted["task"])
		self.assertTrue(task["permitted_actions"]["can_approve"])
		returned = self.call("return_tender_for_correction", task=submitted["task"], reason="Confirm whether manufacturer authorisation is necessary and update the evidence requirement.", expected_record_version=str(submitted["record_version"]), idempotency_key=fx.key())
		frappe.set_user(fx.OFFICER)
		resub = self.call("submit_tender_for_approval", tender=tender, expected_record_version=str(returned["record_version"]), idempotency_key=fx.key())
		frappe.set_user(fx.HOPF)
		approved = self.call("approve_tender_for_publication", task=resub["task"], expected_record_version=str(resub["record_version"]), idempotency_key=fx.key())
		self.assertEqual(approved["action"], "approved")
		view = self.call("get_approved_tender", tender=tender)
		self.assertEqual(view["publication_handoff"]["status"], "Ready")
		history = self.call("get_tender_history", tender=tender)
		self.assertEqual(len(history["versions"]), 2)

	def test_an_outsider_reads_a_record_as_not_found_data_never_a_404(self):
		"""§11.3 TPR_NOT_FOUND at the API boundary (KT-STD-001 §3A.2): the
		service masks with DoesNotExistError; the request-shaped read answers
		the verdict as data so the page paints it inline without a modal."""
		prep = fx.prepared()
		handoff = frappe.db.get_value("Prepared Tender", prep["tender"], "requisition_handoff")
		frappe.set_user(fx.OUTSIDER)
		for method, args in (("get_tender_editor", {"tender": prep["tender"]}), ("get_approved_tender", {"tender": prep["tender"]}), ("get_tender_approval_task", {"task": "TPK-NOPE"}), ("get_tender_compatibility", {"handoff": handoff}), ("get_tender_preview", {"tender": prep["tender"], "output": "invitation"})):
			out = self.call(method, **args)
			self.assertEqual(out, {"outcome": "NOT_FOUND", "message": "Tender not found."}, method)
		frappe.set_user(fx.AUDITOR)
		self.assertEqual(self.call("get_tender_editor", tender="TPR-NOPE")["outcome"], "NOT_FOUND")
		self.assertEqual(self.call("get_tender_editor", tender=prep["tender"])["outcome"], "OK")

	def test_no_business_gate_admits_administrator_or_system_manager_without_an_assignment(self):
		"""SMOKE-19 / TPR-AC-030/040."""
		handoff = fx.authorised_handoff()
		for user in ("Administrator",):
			frappe.set_user(user)
			with self.assertRaises(frappe.DoesNotExistError):
				self.call("prepare_tender", handoff=handoff, idempotency_key=fx.key())
			self.assertEqual(self.call("get_tender_preparation_workspace")["outcome"], "OK")  # technical read
		self.assertEqual(frappe.db.count("Prepared Tender"), 0)

	def test_the_technical_acknowledgment_is_system_manager_only(self):
		app = fx.approved()
		frappe.set_user(fx.HOPF)
		with self.assertRaises(Exception):
			self.call("acknowledge_tender_publication_consumed_technical", tender=app["tender"], correlation_id=fx.key(), published_on="2102-02-01")
		frappe.set_user("Administrator")
		out = self.call("acknowledge_tender_publication_consumed_technical", tender=app["tender"], correlation_id=fx.key(), published_on="2102-02-01")
		self.assertEqual(out["action"], "acknowledged")


class TestApiSurface(TenderCase):
	def test_api_surface_declares_every_parameter(self):
		tree = ast.parse(inspect.getsource(api))
		for node in ast.walk(tree):
			if isinstance(node, ast.FunctionDef) and any(isinstance(d, ast.Call) or isinstance(d, ast.Attribute) for d in node.decorator_list):
				self.assertIsNone(node.args.kwarg, f"{node.name} declares **kwargs")
				self.assertIsNone(node.args.vararg, f"{node.name} declares *args")

	def test_no_parameter_is_named_bare_values_or_a_scope(self):
		tree = ast.parse(inspect.getsource(api))
		for node in ast.walk(tree):
			if isinstance(node, ast.FunctionDef):
				names = [a.arg for a in node.args.args]
				self.assertNotIn("values", names, node.name)
				for name in names:
					self.assertNotIn("pe_fy", name)
					self.assertNotIn("procuring_entity", name)
					self.assertNotIn("fiscal_year", name)
