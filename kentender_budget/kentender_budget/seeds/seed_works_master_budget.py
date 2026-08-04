# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CLI wrapper — neutralized by MVP-1 Budget preparatory teardown."""

from __future__ import annotations

from typing import Any

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget


def run(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	return upsert_works_master_budget()
