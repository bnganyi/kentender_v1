# Copyright (c) 2026, KenTender and contributors
"""System-generated immutable Strategy references ({PE}-{TYPE}-####)."""

from __future__ import annotations

import re

import frappe
from frappe import _

# Type token → (DocType, fieldname)
REF_TYPE_META: dict[str, tuple[str, str]] = {
	"SP": ("Strategic Plan", "plan_id"),
	"SPV": ("Strategic Plan Version", "plan_version_id"),
	"NODE": ("Strategy Node", "strategy_node_id"),
	"IND": ("Performance Indicator", "indicator_id"),
	"TGT": ("Performance Target", "target_id"),
}

DOCTYPE_REF: dict[str, tuple[str, str]] = {
	dt: (token, field) for token, (dt, field) in REF_TYPE_META.items()
}

REF_RE = re.compile(r"^[A-Z0-9]+-(SP|SPV|NODE|IND|TGT)-\d{4}$")


def site_slug() -> str:
	"""CU-303 — business prefix from the one configured site entity
	(Site Procuring Entity.pe_code, PE-MOH → MOH). Fails closed when the
	site is unconfigured: references are never allocated without identity."""
	code = frappe.db.get_single_value("Site Procuring Entity", "pe_code")
	if not code:
		frappe.throw(_("Configure the site's procuring entity before creating strategy records"))
	code = str(code).strip().upper()
	if code.startswith("PE-"):
		code = code[3:]
	slug = re.sub(r"[^A-Z0-9]", "", code)
	if not slug:
		frappe.throw(_("The site entity code is not usable for references"))
	return slug


def pe_slug(procuring_entity: str | None) -> str:
	"""Business prefix from PE entity_code (PE-MOH → MOH).

	LEGACY (pre-cutover bridge): still exported for kentender_budget's
	budget_reference, which cuts over in CU-4xx. Strategy's own allocation
	uses `site_slug()` and never reads the legacy Procuring Entity store."""
	if not procuring_entity:
		frappe.throw(_("Procuring entity is required to allocate a reference"))
	code = frappe.db.get_value("Procuring Entity", procuring_entity, "entity_code") or procuring_entity
	code = str(code).strip().upper()
	if code.startswith("PE-"):
		code = code[3:]
	slug = re.sub(r"[^A-Z0-9]", "", code)
	if not slug:
		frappe.throw(_("Procuring entity has no usable code for references"))
	return slug


def _max_seq(doctype: str, field: str, prefix: str) -> int:
	# has_column expects the DocType name (not tab-prefixed table name).
	if not frappe.db.has_column(doctype, field):
		return 0
	rows = frappe.db.sql(
		f"SELECT `{field}` FROM `tab{doctype}` WHERE `{field}` LIKE %s",
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
	"""Read tabSeries.current without DocType ORM (Series has no creation column)."""
	row = frappe.db.sql(
		"SELECT `current` FROM `tabSeries` WHERE `name`=%s",
		(series_key,),
	)
	return int(row[0][0]) if row else None


def allocate_reference(type_token: str) -> str:
	"""Allocate the next never-reuse `{SITE}-{TYPE}-####` reference.

	CU-303 — the prefix comes from the one configured site entity; no
	Procuring Entity parameter exists. Uses Frappe naming series (same family
	as Package/Demand). Series is advanced on each call so allocate paths do
	not reuse numbers. On first use for a prefix, the series is seeded past
	any existing max so remapped seed codes are not reissued.
	"""
	from frappe.model.naming import make_autoname

	type_token = (type_token or "").strip().upper()
	if type_token not in REF_TYPE_META:
		frappe.throw(_("Unknown reference type: {0}").format(type_token))
	doctype, field = REF_TYPE_META[type_token]
	slug = site_slug()
	prefix = f"{slug}-{type_token}-"
	series_key = prefix  # Series.name is the prefix including trailing '-'
	# Seed series past current max once (idempotent when series already ahead).
	current_max = _max_seq(doctype, field, prefix)
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
		if not frappe.db.exists(doctype, {field: candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique {0} reference").format(type_token))


def assert_reference_immutable(doc, field: str) -> None:
	"""Block reference edits after first save.

	STR-CHG-001 v1.6 cleanup: the admin-correction escape hatch this used to
	honour (`correct_reference`/`can_correct_reference`) was dead code with
	zero live callers and referenced a stale pre-v1.5 "Returned" status —
	removed outright rather than fixed forward, since nothing exercises it."""
	if doc.is_new():
		return
	if not doc.has_value_changed(field):
		return
	frappe.throw(
		_("{0} is system-generated and cannot be edited").format(frappe.unscrub(field)),
		frappe.ValidationError,
	)


def ensure_doc_reference(doc, type_token: str, field: str) -> str:
	"""Assign reference on insert when empty. Returns the reference value."""
	current = (doc.get(field) or "").strip()
	if current:
		return current
	ref = allocate_reference(type_token)
	doc.set(field, ref)
	return ref


def _plan_id_for_doc(doc) -> str | None:
	"""Resolve the owning Strategic Plan id for any Strategy-owned document."""
	if doc.doctype == "Strategic Plan":
		return doc.name if not doc.is_new() else None
	if doc.doctype == "Strategic Plan Version":
		return doc.get("plan_id")
	plan_version_id = _plan_version_id_for_doc(doc)
	if not plan_version_id:
		return None
	return frappe.db.get_value("Strategic Plan Version", plan_version_id, "plan_id")


def _plan_version_id_for_doc(doc) -> str | None:
	if doc.doctype in ("Strategic Plan Version", "Strategy Node", "Performance Indicator"):
		return doc.get("plan_version_id")
	if doc.doctype == "Performance Target":
		indicator_id = doc.get("indicator_id")
		if not indicator_id:
			return None
		return frappe.db.get_value("Performance Indicator", indicator_id, "plan_version_id")
	return None


def before_insert_assign_reference(doc) -> None:
	meta = DOCTYPE_REF.get(doc.doctype)
	if not meta:
		return
	type_token, field = meta
	ensure_doc_reference(doc, type_token, field)


def validate_reference_field(doc) -> None:
	meta = DOCTYPE_REF.get(doc.doctype)
	if not meta:
		return
	_type_token, field = meta
	assert_reference_immutable(doc, field)
	code = (doc.get(field) or "").strip()
	if not code:
		frappe.throw(_("{0} is required").format(frappe.unscrub(field)))


