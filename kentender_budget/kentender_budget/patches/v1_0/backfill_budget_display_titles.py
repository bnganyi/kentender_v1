import re

import frappe


_HASH_LIKE = re.compile(r"^[A-Za-z0-9]{8,}$")


def execute():
	_backfill_budget()
	_backfill_budget_line()


def _looks_hash_like(value):
	text = (value or "").strip()
	return bool(text and _HASH_LIKE.fullmatch(text))


def _backfill_budget():
	if not frappe.db.table_exists("Budget"):
		return
	rows = frappe.get_all(
		"Budget",
		fields=["name", "budget_name", "procuring_entity", "fiscal_year"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.budget_name):
			continue
		entity = (row.procuring_entity or "").strip()
		year = row.fiscal_year or ""
		if entity and year:
			new_title = f"{entity} Budget {year}"
		elif entity:
			new_title = f"{entity} Budget {counter:03d}"
		elif year:
			new_title = f"Budget {year}"
		else:
			new_title = f"Budget {counter:03d}"
		counter += 1
		frappe.db.set_value("Budget", row.name, "budget_name", new_title, update_modified=False)


def _backfill_budget_line():
	if not frappe.db.table_exists("Budget Line"):
		return
	rows = frappe.get_all(
		"Budget Line",
		fields=["name", "budget_line_name", "budget_line_code"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.budget_line_name):
			continue
		code = (row.budget_line_code or "").strip()
		new_title = code if code else f"Budget Line {counter:03d}"
		counter += 1
		frappe.db.set_value(
			"Budget Line",
			row.name,
			"budget_line_name",
			new_title,
			update_modified=False,
		)
