# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""System-generated Budget references ({PE}-BUD-####)."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.naming import make_autoname

from kentender_strategy.services.strategy_reference import pe_slug

BUD_REF_RE = re.compile(r"^[A-Z0-9]+-BUD-\d{4}$")


def _max_seq(prefix: str) -> int:
	if not frappe.db.has_column("Budget", "generated_reference"):
		return 0
	rows = frappe.db.sql(
		"SELECT `generated_reference` FROM `tabBudget` WHERE `generated_reference` LIKE %s",
		(prefix + "%",),
	)
	max_seq = 0
	for (raw,) in rows:
		if not raw or not str(raw).startswith(prefix):
			continue
		tail = str(raw)[len(prefix) :]
		if tail.isdigit():
			max_seq = max(max_seq, int(tail))
	return max_seq


def _series_current(series_key: str) -> int | None:
	row = frappe.db.sql(
		"SELECT `current` FROM `tabSeries` WHERE `name`=%s",
		(series_key,),
	)
	return int(row[0][0]) if row else None


def allocate_budget_reference(procuring_entity: str) -> str:
	"""Allocate next never-reuse `{PE}-BUD-####` for the entity."""
	slug = pe_slug(procuring_entity)
	prefix = f"{slug}-BUD-"
	series_key = prefix
	current_max = _max_seq(prefix)
	existing_series = _series_current(series_key)
	if existing_series is None and current_max:
		frappe.db.sql(
			"INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, %s)",
			(series_key, current_max),
		)
	elif existing_series is not None and existing_series < current_max:
		frappe.db.sql(
			"UPDATE `tabSeries` SET `current`=%s WHERE `name`=%s",
			(current_max, series_key),
		)
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists("Budget", {"generated_reference": candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique Budget reference"))
