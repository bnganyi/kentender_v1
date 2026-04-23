import re

import frappe
from frappe.model.rename_doc import rename_doc


_HASH_LIKE = re.compile(r"^[A-Za-z0-9]{8,}$")
_SAFE = re.compile(r"[^A-Za-z0-9 _-]+")


def execute():
	_rename_hash_departments()


def _rename_hash_departments():
	if not frappe.db.table_exists("Procuring Department"):
		return
	rows = frappe.get_all(
		"Procuring Department",
		fields=["name", "department_name", "procuring_entity"],
		order_by="modified asc, creation asc",
		limit=100000,
	)
	for row in rows:
		old_name = (row.name or "").strip()
		if not _HASH_LIKE.fullmatch(old_name or ""):
			continue
		base = _sanitize(row.department_name) or _sanitize(row.procuring_entity) or "Department"
		new_name = _next_available_name("Procuring Department", base, old_name)
		if not new_name or new_name == old_name:
			continue
		try:
			rename_doc(
				"Procuring Department",
				old_name,
				new_name,
				force=True,
				merge=False,
				ignore_permissions=True,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "rename_hash_procuring_department_failed")


def _sanitize(value):
	s = _SAFE.sub("", (value or "").strip()).strip()
	s = re.sub(r"\s+", " ", s)
	return s[:100]


def _next_available_name(doctype, base, old_name):
	if not base:
		return None
	if base == old_name:
		return base
	if not frappe.db.exists(doctype, base):
		return base
	idx = 2
	while idx < 10000:
		candidate = f"{base} {idx}"
		if candidate == old_name:
			return candidate
		if not frappe.db.exists(doctype, candidate):
			return candidate
		idx += 1
	return None
