# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""System-generated Demand / Demand Item business codes (DMD-*)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.utils import now_datetime

from kentender_strategy.services.strategy_reference import pe_slug


def allocate_demand_code(procuring_entity: str, *, year: int | None = None) -> str:
	"""Allocate next never-reuse ``DMD-{PE}-{YEAR}-####``."""
	slug = pe_slug(procuring_entity)
	yr = int(year or now_datetime().year)
	prefix = f"DMD-{slug}-{yr}-"
	_sync_series(prefix, _max_seq(prefix))
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists("Demand", {"demand_code": candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique Demand reference"))


def allocate_item_code(demand_code: str, line_idx: int) -> str:
	stem = (demand_code or "").strip().upper()
	if stem.startswith("DMD-"):
		stem = stem[4:]
	return f"DMDITEM-{stem}-{int(line_idx):03d}"


def _max_seq(prefix: str) -> int:
	rows = frappe.db.sql(
		"SELECT `demand_code` FROM `tabDemand` WHERE `demand_code` LIKE %s",
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


def _sync_series(prefix: str, current_max: int) -> None:
	row = frappe.db.sql("SELECT `current` FROM `tabSeries` WHERE `name`=%s", (prefix,))
	existing = int(row[0][0]) if row else None
	if existing is None and current_max:
		frappe.db.sql(
			"INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, %s)",
			(prefix, current_max),
		)
	elif existing is not None and existing < current_max:
		frappe.db.sql(
			"UPDATE `tabSeries` SET `current`=%s WHERE `name`=%s",
			(current_max, prefix),
		)
