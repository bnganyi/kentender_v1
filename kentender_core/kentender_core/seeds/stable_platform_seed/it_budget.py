# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT budget supplement — neutralized by MVP-1 Budget preparatory teardown."""

from __future__ import annotations

from typing import Any


def upsert_it_budget_supplement(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	return {"ok": True, "skipped": True, "reason": "mvp1-budget-teardown"}
