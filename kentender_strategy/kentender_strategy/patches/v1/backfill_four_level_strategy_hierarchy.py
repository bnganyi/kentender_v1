"""Backfill Sub Program strategic_plan and Strategy Objective sub_program for 4-level hierarchy."""

import frappe


def execute():
	_backfill_sub_program_strategic_plan()
	_backfill_objective_sub_programs()


def _backfill_sub_program_strategic_plan():
	if not frappe.db.exists("DocType", "Sub Program"):
		return
	meta = frappe.get_meta("Sub Program")
	if not meta.has_field("strategic_plan"):
		return

	for row in frappe.get_all("Sub Program", fields=["name", "program", "strategic_plan"], limit=100000):
		if row.strategic_plan:
			continue
		if not row.program:
			continue
		plan = frappe.db.get_value("Strategy Program", row.program, "strategic_plan")
		if plan:
			frappe.db.set_value("Sub Program", row.name, "strategic_plan", plan, update_modified=False)


def _backfill_objective_sub_programs():
	if not frappe.db.exists("DocType", "Strategy Objective"):
		return
	meta = frappe.get_meta("Strategy Objective")
	if not meta.has_field("sub_program"):
		return

	objectives = frappe.get_all(
		"Strategy Objective",
		fields=["name", "strategic_plan", "program", "sub_program", "objective_title"],
		limit=100000,
	)
	for obj in objectives:
		if obj.sub_program:
			continue
		if not obj.program or not obj.strategic_plan:
			continue
		sp_name = _ensure_default_sub_program(obj.strategic_plan, obj.program)
		frappe.db.set_value("Strategy Objective", obj.name, "sub_program", sp_name, update_modified=False)


def _ensure_default_sub_program(plan_name: str, program_name: str) -> str:
	existing = frappe.db.get_value(
		"Sub Program",
		{"strategic_plan": plan_name, "program": program_name},
		"name",
		order_by="modified asc",
	)
	if existing:
		return existing

	prog_title = frappe.db.get_value("Strategy Program", program_name, "program_title") or program_name
	doc = frappe.get_doc(
		{
			"doctype": "Sub Program",
			"strategic_plan": plan_name,
			"program": program_name,
			"title": f"{prog_title} — General",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
