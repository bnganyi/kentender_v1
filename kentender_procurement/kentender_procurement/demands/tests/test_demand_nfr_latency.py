# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-NFR-005 — ordinary queue/detail latency at MVP volume (soft evidence)."""

from __future__ import annotations

import time

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.api import get_demand_detail, list_demands_workspace
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	upsert_principal_approved_demand,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles

# Soft target from DIA-NFR-005 — do not hard-fail CI for slight overage.
SOFT_TARGET_SECONDS = 2.0
HARD_CEILING_SECONDS = 10.0


class TestDemandNfrLatency(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_nfr005_queue_and_detail_latency_soft(self) -> None:
		"""DIA-NFR-005 — list + detail timed; soft ≤2s, hard ceiling for pathology."""
		frappe.set_user("Administrator")
		seed = upsert_principal_approved_demand(commit=False)
		demand = seed["demand"]

		frappe.set_user(C.USER_MEDICAL)
		t0 = time.perf_counter()
		ws = list_demands_workspace(page=1, page_size=100)
		queue_elapsed = time.perf_counter() - t0
		self.assertTrue(ws.get("ok"))

		t1 = time.perf_counter()
		detail = get_demand_detail(demand=demand)
		detail_elapsed = time.perf_counter() - t1
		self.assertTrue(detail.get("ok"))

		# Record for tracker Evidence (visible in failure messages too).
		frappe.logger("demands_nfr").info(
			"DEM-NFR-005 queue=%.3fs detail=%.3fs soft_target=%.1fs",
			queue_elapsed,
			detail_elapsed,
			SOFT_TARGET_SECONDS,
		)
		self.assertLess(
			queue_elapsed,
			HARD_CEILING_SECONDS,
			msg=f"queue pathological: {queue_elapsed:.3f}s",
		)
		self.assertLess(
			detail_elapsed,
			HARD_CEILING_SECONDS,
			msg=f"detail pathological: {detail_elapsed:.3f}s",
		)
		# Soft note (not a hard fail): store flags for evidence readers.
		frappe.flags.demand_nfr005 = {
			"queue_seconds": round(queue_elapsed, 3),
			"detail_seconds": round(detail_elapsed, 3),
			"soft_target_seconds": SOFT_TARGET_SECONDS,
			"within_soft_target": queue_elapsed <= SOFT_TARGET_SECONDS
			and detail_elapsed <= SOFT_TARGET_SECONDS,
		}
		self.assertIsInstance(frappe.flags.demand_nfr005["queue_seconds"], float)
