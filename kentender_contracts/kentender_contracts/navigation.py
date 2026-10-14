# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract Management's contribution to the shared rail (kentender_core.services.navigation_overrides; FU-CM-58).

Procurement's rail reserves a slot labelled "Contract Management", marked Planned, for this module. When this app is installed it takes the slot over: the item opens
the live `contracts` Page and loses its Planned badge, and the route `contracts` shows the shared rail like every other KenTender page. This app does not edit Procurement's
file and does not depend on Procurement: on a site without it nothing here runs, and `/app/contracts` shows this app's own Workspace Sidebar ("Contracts")."""

from __future__ import annotations


def overrides() -> dict:
	return {"Procurement": {"items": {"Contract Management": {"link_to": "contracts", "link_type": "Page", "route_options": None}}, "routes": ["contracts"]}}
