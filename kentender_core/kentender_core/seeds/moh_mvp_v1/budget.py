# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any


def upsert_budget() -> dict[str, Any]:
	from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio

	# Canonical demo pack only — test-edge budgets stay out of make seed-moh-mvp-v1.
	return upsert_moh_mvp_v1_portfolio(include_test_edges=False)
