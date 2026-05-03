# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Resolve business identifiers (plan_code, template_code, demand_id) to DocType `name` (C4 / API)."""

from __future__ import annotations

import frappe
from frappe import _


def resolve_procurement_plan_name(plan_ref: str) -> str:
	"""Return internal Procurement Plan `name` from `name` or unique `plan_code`."""
	ref = (plan_ref or "").strip()
	if not ref:
		frappe.throw(_("Procurement Plan reference is required."), title=_("Missing plan"))
	if frappe.db.exists("Procurement Plan", ref):
		return ref
	n = frappe.db.get_value("Procurement Plan", {"plan_code": ref}, "name")
	if n:
		return n
	frappe.throw(_("Procurement Plan not found for reference {0}.").format(ref), title=_("Invalid plan"))


def resolve_procurement_template_name(template_ref: str) -> str:
	"""Return internal Procurement Template `name` from `name` or unique `template_code`."""
	ref = (template_ref or "").strip()
	if not ref:
		frappe.throw(_("Procurement Template reference is required."), title=_("Missing template"))
	if frappe.db.exists("Procurement Template", ref):
		return ref
	n = frappe.db.get_value("Procurement Template", {"template_code": ref}, "name")
	if n:
		return n
	frappe.throw(_("Procurement Template not found for reference {0}.").format(ref), title=_("Invalid template"))


def resolve_demand_name(demand_ref: str) -> str:
	"""Return internal Demand `name` from `name` or business `demand_id`."""
	ref = (demand_ref or "").strip()
	if not ref:
		frappe.throw(_("Demand reference is required."), title=_("Missing demand"))
	if frappe.db.exists("Demand", ref):
		return ref
	n = frappe.db.get_value("Demand", {"demand_id": ref}, "name")
	if n:
		return n
	frappe.throw(_("Demand not found for reference {0}.").format(ref), title=_("Invalid demand"))
