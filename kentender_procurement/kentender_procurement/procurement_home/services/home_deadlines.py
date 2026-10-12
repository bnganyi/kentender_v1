# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — upcoming deadlines from explicit stored dates only.

The only source was the retired tender workbench's timeline; until Tenders publishes
a deadline contract this section is honestly empty rather than reading another
module's tables."""

from __future__ import annotations

from typing import Any

DEADLINE_LIMIT = 5


def get_home_deadlines(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	_ = procuring_entity, fiscal_year, user
	return {"ok": True, "items": [], "empty": True}
