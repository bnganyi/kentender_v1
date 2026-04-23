import re

import frappe


_HASH_LIKE = re.compile(r"^[A-Za-z0-9]{8,}$")


def execute():
	_backfill_procuring_department()
	_backfill_procuring_entity()
	_backfill_business_unit()


def _looks_hash_like(value):
	text = (value or "").strip()
	return bool(text and _HASH_LIKE.fullmatch(text))


def _backfill_procuring_department():
	if not frappe.db.table_exists("Procuring Department"):
		return
	rows = frappe.get_all(
		"Procuring Department",
		fields=["name", "department_name", "procuring_entity"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.department_name):
			continue
		entity = (row.procuring_entity or "").strip()
		base = f"{entity} Department" if entity else "Department"
		new_title = f"{base} {counter:03d}"
		counter += 1
		frappe.db.set_value(
			"Procuring Department",
			row.name,
			"department_name",
			new_title,
			update_modified=False,
		)


def _backfill_procuring_entity():
	if not frappe.db.table_exists("Procuring Entity"):
		return
	rows = frappe.get_all(
		"Procuring Entity",
		fields=["name", "entity_code", "entity_name"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.entity_name):
			continue
		code = (row.entity_code or "").strip()
		new_title = code if code else f"Entity {counter:03d}"
		counter += 1
		frappe.db.set_value(
			"Procuring Entity",
			row.name,
			"entity_name",
			new_title,
			update_modified=False,
		)


def _backfill_business_unit():
	if not frappe.db.table_exists("Business Unit"):
		return
	rows = frappe.get_all(
		"Business Unit",
		fields=["name", "unit_name", "department"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	counter = 1
	for row in rows:
		if not _looks_hash_like(row.unit_name):
			continue
		department = (row.department or "").strip()
		base = f"{department} Unit" if department else "Business Unit"
		new_title = f"{base} {counter:03d}"
		counter += 1
		frappe.db.set_value(
			"Business Unit",
			row.name,
			"unit_name",
			new_title,
			update_modified=False,
		)
