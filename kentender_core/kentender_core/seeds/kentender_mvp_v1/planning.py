# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 Planning stage — module-owned seed entry.

PLN-CHG-001 v1.2 §14 (Phase 11): the integrated §14.4–14.6 baseline, driven
through the real Planning commands by the named §14.2 actors. The isolated
profiles (§14.7/§14.8, return/shortfall/stale/successor/publication-failure)
are separate, mutually-exclusive entry points on the module's own seed and
are deliberately not part of this default stage (§14.10).
"""

from __future__ import annotations

from typing import Any


def upsert_planning() -> dict[str, Any]:
	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
		upsert_planning_base,
	)

	return upsert_planning_base(commit=False)
