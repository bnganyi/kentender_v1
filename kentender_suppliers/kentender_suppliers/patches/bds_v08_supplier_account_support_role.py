# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 plan OD-D — the Supplier Organisation form grants read to
"Supplier Account Support Officer", so that Role must exist before the
Supplier Accounts DocTypes sync. kentender_core's `ensure_roles()` creates
every registered role after migrate; this runs it before the model sync."""

from __future__ import annotations


def execute() -> None:
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
