# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Procurement Home API."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_home.services.home_service import build_procurement_home


@frappe.whitelist()
def get_procurement_home(
	procuring_entity: str | None = None,
	fiscal_year: int | str | None = None,
) -> dict[str, Any]:
	"""Permission-scoped Home projection for the Desk page."""
	return build_procurement_home(
		procuring_entity=procuring_entity,
		fiscal_year=fiscal_year,
		user=frappe.session.user,
	)
