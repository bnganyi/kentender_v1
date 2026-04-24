# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C1 — Validate DIA Demand records against a Procurement Template (Cursor Pack C1)."""

import frappe
from frappe import _
from frappe.utils import cint, flt
from frappe.utils.data import parse_json

ALLOWED_DEMAND_STATUSES = frozenset(("Approved", "Planning Ready"))


def _parse_json_list(raw, label: str) -> list:
	if raw in (None, ""):
		frappe.throw(_("{0} is missing on the template.").format(label), title=_("Invalid template"))
	parsed = parse_json(raw) if isinstance(raw, str) else raw
	if not isinstance(parsed, list):
		frappe.throw(_("{0} must be a JSON list.").format(label), title=_("Invalid template"))
	return parsed


def validate_demands_for_template(template_id: str, demand_ids: list[str]) -> None:
	"""Raise ValidationError if any demand is not eligible for the template."""
	if not template_id:
		frappe.throw(_("Procurement Template is required."), title=_("Missing template"))
	if not demand_ids:
		frappe.throw(_("At least one demand is required."), title=_("Missing demands"))

	if not frappe.db.exists("Procurement Template", template_id):
		frappe.throw(_("Procurement Template does not exist."), title=_("Invalid template"))

	tmpl = frappe.get_doc("Procurement Template", template_id)
	# Match template defaults: unset is_active treated as active; only explicit off is inactive.
	if tmpl.get("is_active") is not None and cint(tmpl.is_active) == 0:
		frappe.throw(_("Procurement Template is not active."), title=_("Inactive template"))

	demand_types = _parse_json_list(tmpl.applicable_demand_types, _("Applicable Demand Types"))
	req_types = _parse_json_list(tmpl.applicable_requisition_types, _("Applicable Requisition Types"))

	for demand_id in demand_ids:
		if not demand_id or not frappe.db.exists("Demand", demand_id):
			frappe.throw(_("Demand {0} does not exist.").format(demand_id or ""), title=_("Invalid demand"))

		d = frappe.db.get_value(
			"Demand",
			demand_id,
			("name", "status", "demand_type", "requisition_type", "budget_line", "total_amount"),
			as_dict=True,
		)

		if d.status not in ALLOWED_DEMAND_STATUSES:
			frappe.throw(
				_("Demand {0} must be Approved or Planning Ready for planning (current: {1}).").format(
					demand_id, d.status or ""
				),
				title=_("Demand not eligible"),
			)

		if d.demand_type not in demand_types:
			frappe.throw(
				_("Demand {0}: demand type {1} is not allowed by this template.").format(
					demand_id, d.demand_type or ""
				),
				title=_("Template mismatch"),
			)

		if d.requisition_type not in req_types:
			frappe.throw(
				_("Demand {0}: requisition type {1} is not allowed by this template.").format(
					demand_id, d.requisition_type or ""
				),
				title=_("Template mismatch"),
			)

		if not d.budget_line:
			frappe.throw(
				_("Demand {0} has no Budget Line set.").format(demand_id),
				title=_("Invalid demand"),
			)

		if not frappe.db.exists("Budget Line", d.budget_line):
			frappe.throw(
				_("Demand {0}: Budget Line {1} does not exist.").format(demand_id, d.budget_line),
				title=_("Invalid budget line"),
			)

		bl_active = frappe.db.get_value("Budget Line", d.budget_line, "is_active")
		if bl_active is not None and int(bl_active) == 0:
			frappe.throw(
				_("Demand {0}: Budget Line {1} is not active.").format(demand_id, d.budget_line),
				title=_("Invalid budget line"),
			)

		if flt(d.total_amount or 0) <= 0:
			frappe.throw(
				_("Demand {0} must have a positive total amount for packaging.").format(demand_id),
				title=_("Invalid demand"),
			)

		if frappe.db.sql(
			"""select name from `tabProcurement Package Line`
			where demand_id = %s and ifnull(is_active, 1) = 1 limit 1""",
			demand_id,
		):
			frappe.throw(
				_("Demand {0} is already linked to an active package line.").format(demand_id),
				title=_("Already packaged"),
			)