# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — the two thin sibling-module gateways: every call
forwards to the sibling's *published* contract unchanged, patched at the
seam (focused unit tests; the real contracts are exercised by
`test_gateway_contracts.py` and the owning sibling's own suite)."""

from __future__ import annotations

from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import eligibility_gateway, funding_gateway


class TestEligibilityGateway(IntegrationTestCase):
	def test_get_requisition_eligible_plan_item_forwards(self):
		with patch(
			"kentender_procurement.procurement_planning.services.plan_requisition.get_requisition_eligible_plan_item",
			return_value={"eligible": True},
		) as mocked:
			result = eligibility_gateway.get_requisition_eligible_plan_item("PPI-MOH-2027-033")
			mocked.assert_called_once_with(plan_item_id="PPI-MOH-2027-033")
			self.assertEqual(result, {"eligible": True})

	def test_record_requisition_drawdown_forwards_every_argument(self):
		with patch(
			"kentender_procurement.procurement_planning.services.plan_requisition.record_requisition_drawdown",
			return_value={"ok": True},
		) as mocked:
			eligibility_gateway.record_requisition_drawdown(
				plan_item_id="PPI-1", requisition_reference="REQ-1", requesting_org_unit="OU-1",
				allocations=[{"plan_source_allocation_id": "PSA-1", "quantity": 1, "amount": 1}],
				expected_record_version=0, idempotency_key="key-1",
			)
			mocked.assert_called_once_with(
				plan_item_id="PPI-1", requisition_reference="REQ-1", requesting_org_unit="OU-1",
				allocations=[{"plan_source_allocation_id": "PSA-1", "quantity": 1, "amount": 1}],
				expected_record_version=0, idempotency_key="key-1",
			)


class TestFundingGateway(IntegrationTestCase):
	def test_check_funding_always_names_this_module_as_caller(self):
		with patch("kentender_budget.api.budget_api.check_funding", return_value={"all_sufficient": True}) as mocked:
			funding_gateway.check_funding(
				plan_item="PPI-1", plan_version="PLN-1-V1", source_set_hash="hash-1",
				allocations=[], correlation_id="corr-1", caller_reference="REQ-1",
			)
			mocked.assert_called_once_with(
				plan_item="PPI-1", plan_version="PLN-1-V1", source_set_hash="hash-1", allocations=[],
				correlation_id="corr-1", calling_module="Procurement Requisitions", caller_reference="REQ-1",
			)

	def test_reserve_funding_forwards(self):
		with patch("kentender_budget.api.budget_api.reserve_funding", return_value={"ok": True}) as mocked:
			funding_gateway.reserve_funding(token="tok-1", source_set_hash="hash-1", idempotency_key="key-1")
			mocked.assert_called_once_with(token="tok-1", source_set_hash="hash-1", idempotency_key="key-1")

	def test_release_reservation_names_the_revocation_event_type(self):
		with patch("kentender_budget.services.budget_commitment_contracts.release_reservation", return_value={"ok": True}) as mocked:
			funding_gateway.release_reservation(
				reservation="RSV-1", amount=None, downstream_event_id="REQ-1", idempotency_key="key-1",
			)
			mocked.assert_called_once_with(
				reservation="RSV-1", amount=None, downstream_event_id="REQ-1",
				downstream_event_type="ProcurementRequisitionRevoked", idempotency_key="key-1",
			)
