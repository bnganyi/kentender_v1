# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §10 — request-shaped endpoint tests.

The NDS-914 class: `frappe.handler` hands a whitelisted method the whole
`form_dict` — `cmd` and `csrf_token` included — and only trims it when the
method declares no `**kwargs`. These tests drive the Requisitions endpoints
exactly the way the framework does (`execute_cmd` over a populated
`form_dict`, JSON payloads as strings), and an AST guard keeps `**kwargs`
out of the API surface permanently.
"""

from __future__ import annotations

import ast
import json
import os

import frappe
from frappe.handler import execute_cmd
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.tests import fixtures as fx

API = "kentender_procurement.procurement_requisitions.api"


class RequestShapedCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()
		self.addCleanup(fx.wipe_requisition_rows)
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(setattr, frappe.local, "form_dict", frappe._dict())

	def call(self, method: str, **args):
		"""The framework's own path: form_dict carries cmd + csrf_token, and a
		POST request object is present the way it is on every real command."""
		frappe.local.form_dict = frappe._dict(cmd=f"{API}.{method}", csrf_token="irrelevant-but-present-on-every-post", **args)
		had_request = hasattr(frappe.local, "request")
		if not had_request:
			frappe.local.request = frappe._dict(method="POST", path=f"/api/method/{API}.{method}", headers={})
			self.addCleanup(delattr, frappe.local, "request")
		return execute_cmd(f"{API}.{method}")

	def key(self) -> str:
		return fx.key()


class TestTheFullRequisitionJourneyOverTheRequestPath(RequestShapedCase):
	def test_prepare_through_consumption_with_json_payloads(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		self.assertEqual(self.call("get_requisition_workspace", workspace_filters=json.dumps({}))["outcome"], "OK")
		self.assertEqual(self.call("get_start_preview", plan_item_id=item_id)["state"], "ready")
		prepared = self.call("prepare_it_equipment_requisition", plan_item_id=item_id, idempotency_key=self.key())
		requisition = prepared["requisition"]

		view = self.call("get_requisition_record", requisition=requisition)
		self.call(
			"save_requisition_summary", requisition=requisition,
			summary_values=json.dumps({"delivery_location": fx.delivery_location(), "latest_delivery_date": "2102-04-30"}),
			expected_record_version=str(view["header"]["version_record_version"]), idempotency_key=self.key(),
		)
		view = self.call("get_requisition_record", requisition=requisition)
		rows = [{"drawdown_line_id": r["drawdown_line_id"], "quantity": str(r["quantity"]), "intended_use": "Clinical training for department staff"} for r in view["equipment"]["add_rows"]]
		added = self.call("add_same_specification_items", requisition=requisition, shared_values=json.dumps({"equipment_category": "Laptop", "item_name": "Business laptops"}), item_rows=json.dumps(rows), expected_record_version=str(view["package_record_version"]), idempotency_key=self.key())
		self.assertEqual(added["review_state"], "Review required")

		view = self.call("get_requisition_record", requisition=requisition)
		technical, acceptance, support = fx.visible_proposal(view)
		req = view["requirements"]
		applied = self.call(
			"apply_selected_requirement_package", requisition=requisition, profile_key=req["profile_key"], profile_version=req["profile_version"], proposal_digest=req["proposal_digest"],
			technical_rows=json.dumps(technical), acceptance_rows=json.dumps(acceptance), support_values=json.dumps(support),
			expected_record_version=str(view["package_record_version"]), idempotency_key=self.key(),
		)
		self.assertEqual(applied["review_state"], "Reviewed")

		sent = self.call("send_for_department_approval", requisition=requisition, expected_record_version=str(fx.root_version(requisition)), idempotency_key=self.key())
		frappe.set_user(fx.HOD)
		submitted = self.call("submit_requisition_to_procurement", requisition=requisition, task=sent["task"], expected_record_version=str(fx.root_version(requisition)), idempotency_key=self.key())
		frappe.set_user(fx.HOPF)
		task_view = self.call("get_procurement_authorisation_task", task=submitted["task"])
		self.assertEqual(task_view["result"]["title"], "Ready to authorise")
		authorised = self.call("authorise_requisition", requisition=requisition, task=submitted["task"], expected_record_version=str(fx.root_version(requisition)), idempotency_key=self.key())
		self.assertEqual(authorised["action"], "authorised")
		self.assertEqual(self.call("get_requisition_record", requisition=requisition)["kind"], "authorised")

		# AUD-REQ-001: consumption has no web endpoint — only Tenders' own Start command consumes a handoff.
		frappe.set_user(fx.HOPF)
		with self.assertRaises(Exception):
			self.call("record_handoff_consumption", handoff_name=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=self.key())
		self.assertFalse(frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "consumed_at"))


class TestNoWhitelistedEndpointTakesKwargs(IntegrationTestCase):
	def test_api_surface_declares_every_parameter(self):
		api_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api.py")
		tree = ast.parse(open(api_path, encoding="utf-8").read())
		offenders = []
		whitelisted = 0
		for node in ast.walk(tree):
			if not isinstance(node, ast.FunctionDef):
				continue
			decorated = any(
				(isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "whitelist") or getattr(d, "attr", "") == "whitelist"
				for d in node.decorator_list
			)
			if not decorated:
				continue
			whitelisted += 1
			if node.args.kwarg is not None:
				offenders.append(node.name)
		self.assertGreater(whitelisted, 0, "no whitelisted endpoints found — scan broken?")
		self.assertEqual(offenders, [], f"**kwargs on a whitelisted endpoint forwards cmd/csrf_token into the service (the NDS-914 class): {offenders}")

	def test_no_parameter_is_named_bare_values(self):
		"""A form-encoded field named `values` shadows `frappe._dict.values()`
		on `frappe.local.form_dict` (documented in `procurement_planning.api`'s
		own `save_direct_requirement`) — every JSON-payload parameter here
		must be named for what it carries instead."""
		api_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api.py")
		tree = ast.parse(open(api_path, encoding="utf-8").read())
		offenders = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and any(a.arg == "values" for a in node.args.args)]
		self.assertEqual(offenders, [], f"parameter literally named 'values' shadows form_dict.values(): {offenders}")
