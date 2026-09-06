# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement rail availability states (separate from authorization).

States
------
available              — normal menu + functional module
planned                — visible with Planned badge + capability overview route
disabled_for_deployment — not shown in menu
forbidden_for_user     — not shown (authorization); never conflated with availability

Availability and authorization must not share the same flag.
"""

from __future__ import annotations

from typing import Any

# Menu labels that are Planned (badge + coming-soon capability overview).
PLANNED_SIDEBAR_LABELS: frozenset[str] = frozenset(
	{
		"Home",
		"Analytics",
		"Evaluation",
		"Awards",
		"Contract Management",
		"Supplier Management",
		"Tender Configurations",
	}
)

# Labels / section names omitted from the rail for this deployment.
# Configuration + children are removed from procurement.json (disabled_for_deployment).
DISABLED_FOR_DEPLOYMENT_LABELS: frozenset[str] = frozenset(
	{
		"Configuration",
		"Governance & Configuration",
		"Strategy Alignment (full)",
		"Budget & Funding (full)",
		"Procurement Templates",
		"Risk Profiles",
		"KPI Profiles",
		"Decision Criteria Profiles",
		"Vendor Management Profiles",
		# Former Configuration child that collided with the renamed Planning label
		# is no longer in the export; keep here as a filter safety net.
	}
)

PLANNED_BADGE_SUFFIX = "Planned"


def apply_availability_to_sidebar_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Filter disabled rows and stamp Planned badge suffix (auth is unchanged)."""
	out: list[dict[str, Any]] = []
	for raw in items:
		label = (raw.get("label") or "").strip()
		if label in DISABLED_FOR_DEPLOYMENT_LABELS:
			continue
		row = dict(raw)
		if label in PLANNED_SIDEBAR_LABELS:
			row["suffix"] = PLANNED_BADGE_SUFFIX
		out.append(row)
	return out
