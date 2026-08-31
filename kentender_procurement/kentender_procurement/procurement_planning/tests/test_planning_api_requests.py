# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §8.2 — request-shaped endpoint tests (Phase 2).

The NDS-914 class: `frappe.handler` hands a whitelisted method the whole
`form_dict` — `cmd` and `csrf_token` included — and only trims it when the
method declares no `**kwargs`. Four NDS endpoints broke over HTTP while 242
direct-service tests passed. These tests therefore drive the Planning
endpoints exactly the way the framework does (`execute_cmd` over a populated
`form_dict`, JSON payloads as strings), and an AST guard keeps `**kwargs` out
of the API surface permanently.
"""

from __future__ import annotations

import ast
import json
import os
from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.handler import execute_cmd
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	needs_intake,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx

API = "kentender_procurement.procurement_planning.api"


def key() -> str:
	return uuid4().hex


class RequestShapedCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(setattr, frappe.local, "form_dict", frappe._dict())
		for target, attr, value in (
			(budget_gateway, "eligible_line_ids", {fx.BUDGET_LINE}),
			(needs_intake, "current_accepted_sources", []),
		):
			patched = patch.object(target, attr, return_value=value)
			patched.start()
			self.addCleanup(patched.stop)

	def call(self, method: str, **args):
		"""The framework's own path: form_dict carries cmd + csrf_token, and a
		POST request object is present the way it is on every real command."""
		frappe.local.form_dict = frappe._dict(
			cmd=f"{API}.{method}",
			csrf_token="irrelevant-but-present-on-every-post",
			**args,
		)
		had_request = hasattr(frappe.local, "request")
		if not had_request:
			frappe.local.request = frappe._dict(
				method="POST", path=f"/api/method/{API}.{method}", headers={}
			)
			self.addCleanup(delattr, frappe.local, "request")
		return execute_cmd(f"{API}.{method}")


class TestEndpointsSurviveTheFrameworksTransportFields(RequestShapedCase):
	def test_the_full_dpp_journey_over_the_request_path(self):
		frappe.set_user(fx.AUTHOR)
		opened = self.call(
			"open_departmental_plan",
			procuring_entity=fx.PE,
			organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN,
			idempotency_key=key(),
		)
		self.assertTrue(opened["ok"])
		added = self.call(
			"save_direct_requirement",
			dpp_version=opened["current_version"],
			entry_values=json.dumps(fx.direct_values()),  # JSON string, as over HTTP
			expected_record_version=str(opened["record_version"]),
			idempotency_key=key(),
		)
		self.assertEqual(added["action"], "direct_added")
		frappe.set_user(fx.HOD)
		submitted = self.call(
			"submit_departmental_plan",
			dpp_version=opened["current_version"],
			certification_confirmed="1",  # checkbox arrives as a string
			expected_record_version=str(added["record_version"]),
			idempotency_key=key(),
		)
		self.assertEqual(submitted["action"], "submitted")
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = self.call(
			"accept_departmental_plan",
			task=task.name,
			classifications=json.dumps({added["entry_id"]: "Goods"}),
			task_token=task.task_token,
			idempotency_key=key(),
		)
		self.assertEqual(accepted["action"], "accepted")

	def test_return_over_the_request_path(self):
		frappe.set_user(fx.AUTHOR)
		opened = self.call(
			"open_departmental_plan", procuring_entity=fx.PE,
			organisation_unit=fx.OU_ALPHA, financial_year=fx.FY_OPEN,
			idempotency_key=key(),
		)
		added = self.call(
			"save_direct_requirement", dpp_version=opened["current_version"],
			entry_values=json.dumps(fx.direct_values()),
			expected_record_version=str(opened["record_version"]),
			idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = self.call(
			"submit_departmental_plan", dpp_version=opened["current_version"],
			certification_confirmed="true",
			expected_record_version=str(added["record_version"]),
			idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		returned = self.call(
			"return_departmental_plan",
			task=task.name,
			issues=json.dumps([
				{
					"entry_id": added["entry_id"],
					"problem": "Amount unsupported",
					"correction": "Align the amount with the budget line.",
				}
			]),
			task_token=task.task_token,
			idempotency_key=key(),
		)
		self.assertEqual(returned["action"], "returned")

	def test_resolve_planning_context_is_reachable(self):
		frappe.set_user(fx.PLANNER)
		result = self.call("resolve_planning_context")
		self.assertIn("procuring_entities", result)

	def test_the_finance_confirmation_journey_over_the_request_path(self):
		frappe.set_user(fx.AUTHOR)
		opened = self.call(
			"open_departmental_plan", procuring_entity=fx.PE,
			organisation_unit=fx.OU_ALPHA, financial_year=fx.FY_OPEN,
			idempotency_key=key(),
		)
		added = self.call(
			"save_direct_requirement", dpp_version=opened["current_version"],
			entry_values=json.dumps(fx.direct_values()),
			expected_record_version=str(opened["record_version"]), idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = self.call(
			"submit_departmental_plan", dpp_version=opened["current_version"],
			certification_confirmed="true",
			expected_record_version=str(added["record_version"]), idempotency_key=key(),
		)
		dpp_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = self.call(
			"accept_departmental_plan", task=dpp_task.name,
			classifications=json.dumps({added["entry_id"]: "Goods"}),
			task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = self.call("get_annual_plan", plan_reference=accepted["annual_plan"])
		formed = self.call(
			"form_plan_items", plan_version=accepted["annual_plan_version"],
			dpp_entries=json.dumps([plan["unallocated_sources"][0]["dpp_entry"]]),
			mode="each", expected_record_version=str(plan["record_version"]), idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		item = self.call("get_plan_item", plan_item_id=item_id)
		self.call(
			"save_plan_item", plan_item=item_id,
			item_values=json.dumps({
				"title": "Direct requirement", "description": "Assess and remediate the direct requirement.",
				"strategic_objective": fx.STRATEGY_OBJECTIVE, "aggregation_reason": "",
				"invitation_date": "2098-08-01", "bid_opening_date": "2098-08-15",
				"evaluation_completion_date": "2098-09-01", "award_approval_date": "2098-09-10",
				"award_notification_date": "2098-09-15", "contract_signing_date": "2098-10-01",
				"delivery_completion_date": "2098-10-15",
			}),
			expected_record_version=str(item["record_version"]), idempotency_key=key(),
		)
		item = self.call("get_plan_item", plan_item_id=item_id)
		requested = self.call(
			"request_finance_confirmation", plan_item=item_id,
			expected_record_version=str(item["record_version"]), idempotency_key=key(),
		)
		self.assertEqual(requested["action"], "requested")

		frappe.set_user(fx.BUDGET_OFFICER)
		finance_task = frappe.get_doc("Plan Finance Task", requested["task"])
		read = self.call("get_finance_task", task=finance_task.name)
		self.assertTrue(read["all_sufficient"])
		confirmed = self.call(
			"confirm_funding", task=finance_task.name, task_token=finance_task.task_token,
			check_token=read["budget_check_token"], idempotency_key=key(),
		)
		self.assertEqual(confirmed["action"], "confirmed")


class TestNoWhitelistedEndpointTakesKwargs(IntegrationTestCase):
	def test_api_surface_declares_every_parameter(self):
		api_path = os.path.join(
			os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api.py"
		)
		tree = ast.parse(open(api_path, encoding="utf-8").read())
		offenders = []
		whitelisted = 0
		for node in ast.walk(tree):
			if not isinstance(node, ast.FunctionDef):
				continue
			decorated = any(
				(isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "whitelist")
				or getattr(d, "attr", "") == "whitelist"
				for d in node.decorator_list
			)
			if not decorated:
				continue
			whitelisted += 1
			if node.args.kwarg is not None:
				offenders.append(node.name)
		self.assertGreater(whitelisted, 0, "no whitelisted endpoints found — scan broken?")
		self.assertEqual(
			offenders, [],
			"**kwargs on a whitelisted endpoint forwards cmd/csrf_token into the "
			f"service (the NDS-914 class): {offenders}",
		)
