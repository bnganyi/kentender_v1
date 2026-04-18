"""Central business ID generation for KenTender (Phase C).

Format: PREFIX-ENTITY-YEAR-XXXX (four-digit sequence).

Counters are persisted in DocType `Business ID Counter` (one row per prefix / entity / year).
"""

from __future__ import annotations

import hashlib
import re
from typing import Union

import frappe
from frappe import _
from frappe.utils import get_table_name

_DOCTYPE = "Business ID Counter"


def _normalize_year(year: Union[int, str]) -> int:
	y = int(year)
	if y < 2000 or y > 2100:
		frappe.throw(_("Year must be between 2000 and 2100"))
	return y


def _counter_key(prefix: str, entity: str, year: int) -> str:
	raw = f"{prefix}\0{entity}\0{year}".encode("utf-8")
	return hashlib.sha256(raw).hexdigest()


def generate_business_id(prefix: str, entity: str, year: Union[int, str]) -> str:
	"""Return the next business ID for the given prefix, entity code, and year.

	Example: ``REQ-MOE-2026-0001``
	"""
	prefix = (prefix or "").strip()
	entity = (entity or "").strip()
	if not prefix:
		frappe.throw(_("prefix is required"))
	if not entity:
		frappe.throw(_("entity is required"))
	if not re.match(r"^[\w.-]+$", prefix):
		frappe.throw(_("prefix contains invalid characters"))
	if not re.match(r"^[\w.-]+$", entity):
		frappe.throw(_("entity contains invalid characters"))

	year = _normalize_year(year)
	key = _counter_key(prefix, entity, year)

	frappe.db.begin()
	try:
		seq = _reserve_next_sequence(key, prefix, entity, year)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		raise

	return f"{prefix}-{entity}-{year}-{seq:04d}"


def _reserve_next_sequence(key: str, prefix: str, entity: str, year: int) -> int:
	"""Atomically reserve and return the next sequence number for this key."""
	tbl = get_table_name(_DOCTYPE, wrap_in_backticks=True)

	def _locked_row():
		return frappe.db.sql(
			f"""
			SELECT `name`, `next_number`
			FROM {tbl}
			WHERE `counter_key`=%s
			FOR UPDATE
			""",
			(key,),
			as_dict=True,
		)

	rows = _locked_row()
	if not rows:
		try:
			frappe.get_doc(
				{
					"doctype": _DOCTYPE,
					"counter_key": key,
					"prefix": prefix,
					"entity": entity,
					"year": year,
					"next_number": 2,
				}
			).insert(ignore_permissions=True)
			return 1
		except frappe.DuplicateEntryError:
			rows = _locked_row()

	if not rows:
		frappe.throw(_("Business ID counter row could not be created or loaded"))

	n = int(rows[0].next_number)
	frappe.db.set_value(
		_DOCTYPE,
		rows[0].name,
		"next_number",
		n + 1,
		update_modified=False,
	)
	return n
