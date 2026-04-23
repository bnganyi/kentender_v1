import re

import frappe


_HASH_LIKE = re.compile(r"^[A-Za-z0-9]{8,}$")


def execute():
	_backfill_strategic_plan()
	_backfill_strategy_program()
	_backfill_sub_program()
	_backfill_strategy_objective()
	_backfill_strategy_target()


def _looks_hash_like(value):
	text = (value or "").strip()
	return bool(text and _HASH_LIKE.fullmatch(text))


def _backfill_strategic_plan():
	if not frappe.db.table_exists("Strategic Plan"):
		return
	rows = frappe.get_all(
		"Strategic Plan",
		fields=["name", "strategic_plan_name", "procuring_entity", "start_year", "end_year"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.strategic_plan_name):
			continue
		entity = (row.procuring_entity or "").strip()
		span = ""
		if row.start_year and row.end_year:
			span = f" ({row.start_year}-{row.end_year})"
		elif row.start_year:
			span = f" ({row.start_year})"
		base = entity if entity else "Strategic Plan"
		new_title = f"{base} Plan {counter:03d}{span}"
		counter += 1
		frappe.db.set_value(
			"Strategic Plan",
			row.name,
			"strategic_plan_name",
			new_title,
			update_modified=False,
		)


def _backfill_strategy_program():
	if not frappe.db.table_exists("Strategy Program"):
		return
	rows = frappe.get_all(
		"Strategy Program",
		fields=["name", "program_title", "program_code"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.program_title):
			continue
		code = (row.program_code or "").strip()
		new_title = code if code else f"Program {counter:03d}"
		counter += 1
		frappe.db.set_value(
			"Strategy Program",
			row.name,
			"program_title",
			new_title,
			update_modified=False,
		)


def _backfill_sub_program():
	if not frappe.db.table_exists("Sub Program"):
		return
	rows = frappe.get_all(
		"Sub Program",
		fields=["name", "title", "sub_program_code"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.title):
			continue
		code = (row.sub_program_code or "").strip()
		new_title = code if code else f"Sub-Program {counter:03d}"
		counter += 1
		frappe.db.set_value("Sub Program", row.name, "title", new_title, update_modified=False)


def _backfill_strategy_objective():
	if not frappe.db.table_exists("Strategy Objective"):
		return
	rows = frappe.get_all(
		"Strategy Objective",
		fields=["name", "objective_title", "objective_code"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.objective_title):
			continue
		code = (row.objective_code or "").strip()
		new_title = code if code else f"Objective {counter:03d}"
		counter += 1
		frappe.db.set_value(
			"Strategy Objective",
			row.name,
			"objective_title",
			new_title,
			update_modified=False,
		)


def _backfill_strategy_target():
	if not frappe.db.table_exists("Strategy Target"):
		return
	rows = frappe.get_all(
		"Strategy Target",
		fields=["name", "target_title", "target_code"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.target_title):
			continue
		code = (row.target_code or "").strip()
		new_title = code if code else f"Target {counter:03d}"
		counter += 1
		frappe.db.set_value(
			"Strategy Target",
			row.name,
			"target_title",
			new_title,
			update_modified=False,
		)
