"""Resolve the procurement-method allow-list shared by Planning services."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr


OPEN_TENDER = "Open tender"
REASON_CONFIGURED_DEFAULT = "PROCUREMENT_METHOD_CONFIGURED_DEFAULT"
REASON_DEGRADED_FALLBACK = "PROCUREMENT_METHOD_FALLBACK_OPEN_TENDER"


def _unique(values: list[str]) -> list[str]:
	seen: set[str] = set()
	resolved: list[str] = []
	for value in values:
		label = cstr(value).strip()
		if label and label.casefold() not in seen:
			seen.add(label.casefold())
			resolved.append(label)
	return resolved


def _catalogue_methods() -> list[str]:
	if not frappe.db.exists("DocType", "Procurement Method"):
		return []
	meta = frappe.get_meta("Procurement Method")
	label_field = next(
		(field for field in ("method_name", "procurement_method", "title") if meta.has_field(field)),
		"name",
	)
	filters: dict[str, Any] = {}
	if meta.has_field("enabled"):
		filters["enabled"] = 1
	elif meta.has_field("is_active"):
		filters["is_active"] = 1
	elif meta.has_field("status"):
		filters["status"] = ["in", ["Active", "Enabled"]]
	return _unique(frappe.get_all(
		"Procurement Method", filters=filters, pluck=label_field,
		order_by=f"{label_field} asc", limit_page_length=0,
	))


def _doctype_select_methods() -> list[str]:
	if not frappe.db.exists("DocType", "Procurement Plan Item Version"):
		return []
	field = frappe.get_meta("Procurement Plan Item Version").get_field("procurement_method")
	if not field or cstr(field.fieldtype) != "Select":
		return []
	return _unique(cstr(field.options).splitlines())


def resolve_procurement_methods() -> dict[str, Any]:
	"""Use active catalogue, then schema options, then the Open tender baseline."""
	catalogue = _catalogue_methods()
	schema_options = _doctype_select_methods()
	if catalogue:
		methods, source = _unique(catalogue), "catalogue"
	elif schema_options:
		methods, source = _unique(schema_options), "doctype_options"
	else:
		methods, source = [], "fallback"

	degraded = not catalogue
	if not any(value.casefold() == OPEN_TENDER.casefold() for value in methods):
		methods.insert(0, OPEN_TENDER)
		degraded = True
	recommended = next(
		(value for value in methods if value.casefold() == OPEN_TENDER.casefold()), methods[0]
	)
	return {
		"methods": methods,
		"recommended": recommended,
		"source": source,
		"degraded": degraded,
		"recommendation_reason_code": (
			REASON_DEGRADED_FALLBACK if degraded else REASON_CONFIGURED_DEFAULT
		),
	}


def procurement_method_is_allowed(method: str, contract: dict[str, Any] | None = None) -> bool:
	selected = cstr(method).strip().casefold()
	resolved = contract or resolve_procurement_methods()
	return bool(selected) and any(
		selected == cstr(value).strip().casefold() for value in resolved.get("methods", [])
	)
