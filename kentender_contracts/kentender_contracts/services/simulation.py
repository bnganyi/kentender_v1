# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Is this site a simulation environment? (plan D8, D10, D16; DEC-044)

Simulation stand-ins (the signing provider, the synthetic rule profile, fault switches) answer only where this is true. The platform's
switch is `kt_bds_simulation_environment`, set on every test and demonstration site; `kt_cm_simulation_environment` lets a site that has
no Bid Submission (the Contract-Management-only independence site) switch it on without borrowing another module's name. On a live
site neither is set. Nothing here is ever shown to a user as a banner or label."""

from __future__ import annotations

import frappe
from frappe.utils import cint

FLAGS = ("kt_cm_simulation_environment", "kt_bds_simulation_environment")


def enabled() -> bool:
	return any(cint(frappe.conf.get(flag)) for flag in FLAGS)
