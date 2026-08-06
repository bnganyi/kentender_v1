# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any


def upsert_budget() -> dict[str, Any]:
	from kentender_budget.seeds.kentender_mvp_v1_portfolio import (
		upsert_kentender_mvp_v1_portfolio,
	)

	# Canonical demo pack only — test-edge budgets stay out of make seed.
	return upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
