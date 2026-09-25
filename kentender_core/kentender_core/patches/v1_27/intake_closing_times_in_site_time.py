# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Owner decision 26 Sep 2026 (FU-V127-01) — instants are stored in the site
timezone. The canonical seed stored the departmental-plan and disposal-plan
intake closing times as the UTC equivalent of 23:59:59 EAT (20:59:59), while
the intake gate compares them with the site clock, so those intakes closed
at 20:59 EAT. Only the exact seeded value is moved: an administrator's own
closing time was entered in site time already."""

from __future__ import annotations

import frappe

from kentender_core.services import site_configuration

SEEDED, SITE_TIME = "2026-11-30 20:59:59", "2026-11-30 23:59:59"


def execute():
	for field in (site_configuration.DPP_FLAG_CLOSES_AT, site_configuration.DISPOSAL_FLAG_CLOSES_AT):
		if not frappe.db.has_column("Fiscal Year", field):
			continue
		for name in frappe.get_all("Fiscal Year", filters={field: SEEDED}, pluck="name"):
			frappe.db.set_value("Fiscal Year", name, field, SITE_TIME, update_modified=False)
