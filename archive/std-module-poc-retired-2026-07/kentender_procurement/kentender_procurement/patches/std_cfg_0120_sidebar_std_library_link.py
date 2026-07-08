# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0120 — point Procurement sidebar Official STD Library to std-library page."""

from __future__ import annotations

import json

import frappe


def execute() -> None:
	path = frappe.get_app_path("kentender_procurement", "workspace_sidebar", "procurement.json")
	with open(path, encoding="utf-8") as handle:
		data = json.load(handle)
	changed = False
	for item in data.get("items") or []:
		if str(item.get("label") or "") == "Official STD Library" and item.get("link_to") == "std-engine":
			item["link_to"] = "std-library"
			changed = True
	if changed:
		with open(path, "w", encoding="utf-8") as handle:
			json.dump(data, handle, indent=1)
			handle.write("\n")
