# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The test-environment switch (BDS-CHG-001 v0.8 owner decision OD-C).

Simulated services (the Test Scanner now; the Test Trust Service, Test
Tender Box and test clock later) answer only on a site whose own
site_config sets `kt_bds_simulation_environment: 1`. There is no Desk,
portal or API control, and a production site leaves it unset, so every
simulation stays silent there. Everything a simulation produces says so in
its own words."""

from __future__ import annotations

import frappe
from frappe.utils import cint

CONFIG_KEY = "kt_bds_simulation_environment"


def enabled() -> bool:
	return bool(cint(frappe.conf.get(CONFIG_KEY)))
