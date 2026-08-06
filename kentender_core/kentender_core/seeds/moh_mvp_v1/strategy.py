# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any


def upsert_strategy(*, reset: bool = False) -> dict[str, Any]:
	from kentender_strategy.seeds.moh_mvp_v1_strategy import upsert_moh_mvp_v1_strategy

	return upsert_moh_mvp_v1_strategy(reset=reset)
