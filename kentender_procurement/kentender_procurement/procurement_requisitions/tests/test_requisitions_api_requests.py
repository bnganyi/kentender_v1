# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10 — request-shaped endpoint tests.

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
		if not frappe.db.exists("Delivery Location", "Test Delivery Location — Requisitions"):
			frappe.get_doc({"doctype": "Delivery Location", "location_name": "Test Delivery Location — Requisitions", "address": "1 Test Street", "status": "Active"}).insert(ignore_permissions=True)
		self.location = "Test Delivery Location — Requisitions"
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
	def test_prepare_through_authorise(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)

		workspace = self.call("get_requisition_workspace")
		self.assertEqual(workspace["outcome"], "OK")

		prepared = self.call("prepare_it_equipment_requisition", plan_item_id=item_id, idempotency_key=self.key())
		self.assertTrue(prepared["ok"])

		# `save_requisition_summary` targets the Requisition Version, not the
		# root — read its record_version back rather than assuming it.
		version_record_version = frappe.db.get_value("Requisition Version", prepared["requisition_version"], "record_version")
		summary = self.call(
			"save_requisition_summary", requisition=prepared["requisition"],
			summary_values=json.dumps({"delivery_location": self.location, "latest_delivery_date": "2102-04-30"}),
			expected_record_version=str(version_record_version), idempotency_key=self.key(),
		)
		self.assertEqual(summary["action"], "saved")

		package_record_version = frappe.db.get_value("IT Equipment Requirement Package Version", prepared["package_version"], "record_version")
		added = self.call(
			"add_requisition_item", requisition=prepared["requisition"],
			item_values=json.dumps({"plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 1, "intended_use": "Clinical training"}),
			expected_record_version=str(package_record_version), idempotency_key=self.key(),
		)
		self.assertEqual(added["action"], "added")

		# A baseline rule that proposes no default (Memory, Storage capacity)
		# must be given a value before it can be confirmed — confirming it
		# bare would silently produce a "Confirmed" row requiring nothing.
		VALUE_LESS_DEFAULTS = {"memory": 16, "storage_capacity": 512}
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		for row in package_version.technical_requirements:
			kwargs = {}
			if not row.required_value_json:
				kwargs["confirmation_values"] = json.dumps({"value": VALUE_LESS_DEFAULTS[row.characteristic_key]})
			confirmed = self.call(
				"confirm_proposed_requirement", requisition=prepared["requisition"], technical_requirement_id=row.technical_requirement_id,
				expected_record_version=str(package_version.record_version), idempotency_key=self.key(), **kwargs,
			)
			self.assertEqual(confirmed["action"], "updated")
			package_version.reload()

		acc = self.call(
			"add_acceptance_requirement", requisition=prepared["requisition"],
			acceptance_values=json.dumps({"applies_to_scope": "All items", "check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"}),
			expected_record_version=str(package_version.record_version), idempotency_key=self.key(),
		)
		self.assertEqual(acc["action"], "added")

		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		submitted = self.call("submit_requisition_to_procurement", requisition=prepared["requisition"], expected_record_version=str(root.record_version), idempotency_key=self.key())
		self.assertEqual(submitted["action"], "submitted")

		frappe.set_user(fx.HOPF)
		root.reload()
		authorised = self.call("authorise_requisition", requisition=prepared["requisition"], task=submitted["task"], expected_record_version=str(root.record_version), idempotency_key=self.key())
		self.assertEqual(authorised["action"], "authorised")

		history = self.call("get_requisition_history", requisition=prepared["requisition"])
		self.assertEqual(history["outcome"], "OK")
		self.assertTrue(history["handoff"])

		consumed = self.call(
			"record_handoff_consumption", handoff_name=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1",
			template_key="IT-EQUIPMENT-DEFAULT", template_version="1.0", idempotency_key=self.key(),
		)
		self.assertEqual(consumed["action"], "consumed")


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
