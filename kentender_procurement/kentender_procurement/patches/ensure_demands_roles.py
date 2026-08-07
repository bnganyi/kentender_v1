# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure Demands MVP-1 operational roles exist."""

from __future__ import annotations


def execute() -> None:
	from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles

	ensure_demand_roles()
