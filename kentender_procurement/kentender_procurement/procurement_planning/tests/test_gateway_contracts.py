# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §7.2/§7.3 gateway drift alarms (Phase 2).

The gateways carry the D6 name deltas between the spec's verbs and the
siblings' published contracts. These tests pin the *published* signatures the
gateways depend on, so a Budget or Strategy refactor fails here — in
Planning's own suite — instead of at runtime in a Finance confirmation. Live
end-to-end calls are exercised at the Phase 7/12 checkpoints."""

from __future__ import annotations

import inspect

from frappe.tests import IntegrationTestCase


class TestBudgetContractSignatures(IntegrationTestCase):
	def params(self, func) -> list[str]:
		return list(inspect.signature(func).parameters)

	def test_the_published_budget_contracts_still_carry_the_expected_parameters(self):
		from kentender_budget.api import budget_api

		expected = {
			"list_eligible_budget_lines": {"procuring_entity", "financial_year", "source_org_unit"},
			"check_funding": {
				"plan_item", "plan_version", "finance_task", "source_set_hash",
				"allocations", "correlation_id",
			},
			"reserve_funding": {"token", "finance_task", "source_set_hash", "idempotency_key"},
			"release_reservation": {
				"reservation", "amount", "downstream_event_id",
				"downstream_event_type", "idempotency_key",
			},
			"revalidate_reservations": {
				"reservations", "downstream_event_id", "downstream_event_type",
				"idempotency_key",
			},
		}
		for name, params in expected.items():
			with self.subTest(contract=name):
				func = getattr(budget_api, name)
				missing = params - set(self.params(func))
				self.assertEqual(
					missing, set(),
					f"budget_api.{name} lost parameters the Planning gateway passes",
				)

	def test_the_published_strategy_contracts_still_carry_the_expected_parameters(self):
		from kentender_strategy.services import strategy_consumer

		# CU-306 — resolve_strategy_context is site-local (one site = one PE):
		# no procuring_entity parameter exists any more, and the gateway calls
		# it with no entity argument.
		params = set(self.params(strategy_consumer.resolve_strategy_context))
		self.assertNotIn("procuring_entity", params)
		self.assertIn("effective_date", params)
		self.assertIn(
			"plan_version_id", self.params(strategy_consumer.list_strategy_objectives)
		)
		snapshot_params = set(self.params(strategy_consumer.create_strategy_snapshot))
		self.assertEqual(
			{"plan_version_id", "objective_id", "correlation_key"} - snapshot_params,
			set(),
		)

	def test_gateway_modules_import_only_published_surfaces(self):
		import ast
		import os

		services = os.path.join(
			os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services"
		)
		allowed_prefixes = (
			"kentender_budget.api.budget_api",
			"kentender_strategy.services.strategy_consumer",
		)
		offenders = []
		for filename in ("budget_gateway.py", "strategy_gateway.py"):
			tree = ast.parse(open(os.path.join(services, filename), encoding="utf-8").read())
			for node in ast.walk(tree):
				if isinstance(node, ast.ImportFrom):
					module = node.module or ""
					if module.startswith(("kentender_budget", "kentender_strategy")):
						if not module.startswith(allowed_prefixes):
							offenders.append(f"{filename}: {module}")
		self.assertEqual(offenders, [], f"gateway deep-imports: {offenders}")
