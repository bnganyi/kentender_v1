# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure Demands MVP-1 DocTypes are imported after model sync.

Guards against the legacy DIA teardown patch or orphan cleanup racing a fresh
Module Def install on the same migrate.
"""

from __future__ import annotations

import os

import frappe
from frappe.modules.import_file import import_file_by_path
from frappe.modules.utils import get_module_path

REQUIRED = (
	"demand",
	"demand_item",
	"demand_strategy_reference",
	"demand_value_treatment",
	"demand_funding_allocation",
	"demand_decision",
	"planning_consumption",
)


def execute() -> None:
	if not frappe.db.exists("Module Def", "Demands"):
		return
	base = os.path.join(get_module_path("Demands"), "doctype")
	for folder in REQUIRED:
		json_path = os.path.join(base, folder, f"{folder}.json")
		if not os.path.exists(json_path):
			continue
		import_file_by_path(json_path, force=True, ignore_version=True)
