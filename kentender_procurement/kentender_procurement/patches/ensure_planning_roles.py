# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure Planning MVP-1 operational roles exist."""

from __future__ import annotations


def execute() -> None:
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ensure_planning_roles,
	)

	ensure_planning_roles()
