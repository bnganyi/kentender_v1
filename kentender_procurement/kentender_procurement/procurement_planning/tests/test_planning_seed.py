# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §14 — deterministic seed contract.

The §14 seed is rebuilt in Phase 7 of the v1.12 cycle (tracker PLN-701..703).
Until that phase lands, the v1.2 seed module still targets the retired
PE/context model and cannot run; this module records that honestly rather
than asserting against a seed that no longer exists."""

from __future__ import annotations

import unittest

from frappe.tests import IntegrationTestCase


class TestPlanningSeedContract(IntegrationTestCase):
	@unittest.skip("PLN-CHG-001 v1.12 Phase 7 rebuilds the §14 seed (tracker PLN-701); the v1.2 seed is retired")
	def test_seed_contract_pending_phase_7(self):
		pass
