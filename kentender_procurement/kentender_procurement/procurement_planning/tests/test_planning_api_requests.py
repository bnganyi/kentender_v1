# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.2 — request-shaped endpoint tests (Phase 2).

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
		cls.addClassCleanup(fx.restore_site)

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
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN,
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
			"open_departmental_plan", organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN,
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
		self.assertIn("financial_years", result)
		self.assertNotIn("procuring_entities", result)

	def test_the_finance_confirmation_journey_over_the_request_path(self):
		frappe.set_user(fx.AUTHOR)
		opened = self.call(
			"open_departmental_plan", organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN,
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
			"save_plan_item", plan_item=item_id, item_values=json.dumps(fx.item_values()),
			expected_record_version=str(item["record_version"]), idempotency_key=key(),
		)
		plan = self.call("get_annual_plan", plan_reference=accepted["annual_plan"])
		self.assertTrue(plan["can_request_funding"])
		requested = self.call(
			"request_plan_funding_confirmation", plan_version=plan["version_reference"],
			expected_record_version=str(plan["record_version"]), idempotency_key=key(),
		)
		self.assertEqual(requested["action"], "requested")

		frappe.set_user(fx.FINANCE_OFFICER)
		finance_task = frappe.get_doc("Plan Finance Task", requested["task"])
		read = self.call("get_finance_task", task=finance_task.name)
		self.assertTrue(read["can_confirm"])
		confirmed = self.call(
			"confirm_plan_funding", task=finance_task.name, task_token=finance_task.task_token, idempotency_key=key(),
		)
		self.assertEqual(confirmed["action"], "confirmed")

	def test_the_cascade_endpoints_over_the_request_path(self):
		from kentender_procurement.procurement_planning.services import plan_governance, plan_read

		frappe.set_user(fx.AUTHOR)
		opened = self.call("open_departmental_plan", organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key())
		added = self.call(
			"save_direct_requirement", dpp_version=opened["current_version"], entry_values=json.dumps(fx.direct_values()),
			expected_record_version=str(opened["record_version"]), idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = self.call(
			"submit_departmental_plan", dpp_version=opened["current_version"], certification_confirmed="true",
			expected_record_version=str(added["record_version"]), idempotency_key=key(),
		)
		dpp_task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		accepted = self.call(
			"accept_departmental_plan", task=dpp_task.name, classifications=json.dumps({added["entry_id"]: "Goods"}),
			task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = self.call("get_annual_plan", plan_reference=accepted["annual_plan"])
		formed = self.call(
			"form_plan_items", plan_version=accepted["annual_plan_version"],
			dpp_entries=json.dumps([plan["unallocated_sources"][0]["dpp_entry"]]), mode="each",
			expected_record_version=str(plan["record_version"]), idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		item = self.call("get_plan_item", plan_item_id=item_id)
		self.call("save_plan_item", plan_item=item_id, item_values=json.dumps(fx.item_values()), expected_record_version=str(item["record_version"]), idempotency_key=key())
		plan = self.call("get_annual_plan", plan_reference=accepted["annual_plan"])
		requested = self.call("request_plan_funding_confirmation", plan_version=plan["version_reference"], expected_record_version=str(plan["record_version"]), idempotency_key=key())
		frappe.set_user(fx.FINANCE_OFFICER)
		finance_task = frappe.get_doc("Plan Finance Task", requested["task"])
		self.call("confirm_plan_funding", task=finance_task.name, task_token=finance_task.task_token, idempotency_key=key())
		frappe.set_user(fx.PLANNER)
		plan = self.call("get_annual_plan", plan_reference=accepted["annual_plan"])
		submitted = self.call("submit_consolidated_plan", plan_version=plan["version_reference"], expected_record_version=str(plan["record_version"]), idempotency_key=key())
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = self.call("adopt_and_submit_plan", task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.STATUTORY)
		approved = self.call("approve_annual_plan", task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
		self.assertEqual(approved["publication_result"], "Acknowledged")
		frappe.set_user(fx.PLANNER)
		preview = self.call("preview_forecast_cascade", plan_item=item_id, milestone="bid_opening", new_forecast_date="2101-09-25")
		self.assertEqual(len(preview["rows"]), 6)
		# a three-day shift of two rows keeps award approval (27 Oct) after evaluation (25 Oct)
		confirmed = self.call(
			"confirm_forecast_cascade", plan_item=item_id, milestone="bid_opening", new_forecast_date="2101-09-25",
			included_milestones=json.dumps(["bid_opening", "evaluation_completion"]),
			reason="Tender Preparation confirmed the issue date will slip three days pending template release.",
			expected_record_version=str(preview["record_version"]), idempotency_key=key(),
		)
		self.assertEqual(len(confirmed["revisions"]), 2)
		self.assertTrue(confirmed["cascade_id"])
		publication = frappe.db.get_value("Annual Plan Publication", {"plan_version": accepted["annual_plan_version"]}, "name")
		self.assertEqual(self.call("get_publication_task", publication=publication)["result"], "Acknowledged")


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
